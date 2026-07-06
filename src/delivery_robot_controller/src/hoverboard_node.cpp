#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <cmath>
#include <mutex> 
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <std_msgs/msg/float32.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_ros/transform_broadcaster.hpp>

// Thư viện đọc ghi Serial chuẩn cấu trúc POSIX của Linux
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

using namespace std::chrono_literals;

#define START_FRAME 0xABCD

struct __attribute__((packed)) SerialCommand {
    uint16_t start;
    int16_t  steer;
    int16_t  speed;
    uint16_t checksum;
};


struct __attribute__((packed)) SerialFeedback {
    uint16_t start;
    int16_t  cmd1;
    int16_t  cmd2;
    int16_t  speedR_meas; // Tốc độ đo được bánh phải
    int16_t  speedL_meas; // Tốc độ đo được bánh trái
    int16_t  batVoltage;
    int16_t  boardTemp;
    uint16_t cmdLed;
    uint16_t checksum;
};

class HoverboardNode : public rclcpp::Node {
public:
    HoverboardNode() : Node("hoverboard_node"), serial_fd_(-1) {
        // Khai báo cấu hình cổng Serial
        this->declare_parameter<std::string>("port", "/dev/dc_port");
        this->declare_parameter<int>("baud_rate", 115200);

        // --- KHAI BÁO THÔNG SỐ CƠ KHÍ ROBOT (Thay đổi cho đúng với robot Axioma của bạn) ---
        this->declare_parameter<double>("wheel_radius", 0.0825); // Bán kính bánh xe (mét) - ví dụ bánh 6.5 inch ~ 0.085m
        this->declare_parameter<double>("wheel_separation", 0.44); // Khoảng cách giữa 2 bánh (mét)
        this->declare_parameter<double>("ticks_per_meter", 115.7); // Tỷ lệ quy đổi từ đơn vị firmware sang mét thực tế
        
        std::string port = this->get_parameter("port").as_string();
        int baud = this->get_parameter("baud_rate").as_int();

        wheel_radius_ = this->get_parameter("wheel_radius").as_double();
        wheel_separation_ = this->get_parameter("wheel_separation").as_double();
        ticks_per_meter_ = this->get_parameter("ticks_per_meter").as_double();

        // Khởi tạo kết nối Serial phần cứng
        if (!initSerial(port, baud)) {
            RCLCPP_ERROR(this->get_logger(), "Không thể mở cổng Serial: %s", port.c_str());
            rclcpp::shutdown();
            return;
        }

        RCLCPP_INFO(this->get_logger(), "Đã kết nối thẳng tới Hoverboard qua: %s", port.c_str());

        // Khởi tạo bộ phát TF (Odom -> base_link)
        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

        // Subscriber nhận lệnh điều khiển
        cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10, std::bind(&HoverboardNode::cmdVelCallback, this, std::placeholders::_1));

        // Publishers
        battery_pub_ = this->create_publisher<std_msgs::msg::Float32>("hoverboard/battery_voltage", 10);
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("odom", 10);

        // Khởi tạo mốc thời gian tính tích phân odom
        last_time_ = this->now();

        // Timer gửi lệnh điều khiển (20Hz)
        write_timer_ = this->create_wall_timer(20ms, std::bind(&HoverboardNode::sendControlCommand, this));

        // Luồng đọc Serial độc lập
        read_thread_ = std::thread(&HoverboardNode::readSerialLoop, this);
    }

    ~HoverboardNode() {
        if (read_thread_.joinable()) read_thread_.join();
        if (serial_fd_ != -1) close(serial_fd_);
    }

private:
    bool initSerial(const std::string& port, int baud) {
        serial_fd_ = open(port.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
        if (serial_fd_ == -1) return false;

        struct termios tty;
        if (tcgetattr(serial_fd_, &tty) != 0) return false;

        tty.c_cflag &= ~PARENB; 
        tty.c_cflag &= ~CSTOPB;
        tty.c_cflag &= ~CSIZE;
        tty.c_cflag |= CS8;
        tty.c_cflag |= CREAD | CLOCAL;

        tty.c_iflag &= ~(IXON | IXOFF | IXANY);
        tty.c_lflag &= ~(ECHO | ECHOE | ECHONL | ISIG | ICANON);
        tty.c_oflag &= ~OPOST;

        speed_t b_rate = B115200;
        if (baud == 9600) b_rate = B9600;

        cfsetispeed(&tty, b_rate);
        cfsetospeed(&tty, b_rate);

        return tcsetattr(serial_fd_, TCSANOW, &tty) == 0;
    }

    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        std::lock_guard<std::mutex> lock(mutex_);
        // Chuyển đổi từ m/s và rad/s sang cấu trúc điều khiển của Firmware Feru
        raw_speed_ = static_cast<int16_t>(-msg->linear.x * 3.3);
        raw_steer_ = static_cast<int16_t>(-msg->angular.z * 3.3); // Steer trong firmware tương đương góc quay
    }

    void sendControlCommand() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        SerialCommand cmd;
        cmd.start = START_FRAME;
        cmd.speed = raw_speed_;
        cmd.steer = raw_steer_;
        cmd.checksum = cmd.start ^ cmd.speed ^ cmd.steer;

        if (serial_fd_ != -1) {
            write(serial_fd_, &cmd, sizeof(cmd));
        }
    }

    void processOdometry(int16_t speed_R, int16_t speed_L) {
        rclcpp::Time current_time = this->now();
        double dt = (current_time - last_time_).seconds();
        last_time_ = current_time;

        if (dt <= 0.0) return;

        // 1. Quy đổi tốc độ từ đơn vị cơ sở dữ liệu Hoverboard sang m/s thực tế
        // Chú ý: Firmware Feru thường quy định speedL và speedR có dấu hướng ngược nhau tùy cấu hình động cơ, 
        // dưới đây giả định tiến lên cùng dấu dương (+). Bạn cần test thực tế hướng quay xe.
        double v_right = -static_cast<double>(speed_L) / ticks_per_meter_;
        double v_left = -static_cast<double>(speed_R) / ticks_per_meter_;

        // Động học robot vi sai (Differential Drive Kinematics)
        double v_linear = (v_right + v_left) / 2.0;
        double v_angular = (v_right - v_left) / wheel_separation_;

        // 2. Tính tích phân Euler để tìm vị trí hiện tại (X, Y, Theta)
        double delta_x = (v_linear * cos(th_)) * dt;
        double delta_y = (v_linear * sin(th_)) * dt;
        double delta_th = v_angular * dt;

        x_ += delta_x;
        y_ += delta_y;
        th_ += delta_th;

        // 3. Chuyển đổi góc quay Euler sang Quaternion chuẩn ROS 2
        tf2::Quaternion q;
        q.setRPY(0, 0, th_); // Thêm 180 độ nếu cần điều chỉnh hướng quay

        // 4. Phát tán dữ liệu qua hệ thống tọa độ động TF (Odom -> base_link)
        geometry_msgs::msg::TransformStamped odom_trans;
        odom_trans.header.stamp = current_time;
        odom_trans.header.frame_id = "odom";
        odom_trans.child_frame_id = "base_link";

        odom_trans.transform.translation.x = x_;
        odom_trans.transform.translation.y = y_;
        odom_trans.transform.translation.z = 0.0;
        odom_trans.transform.rotation.x = q.x();
        odom_trans.transform.rotation.y = q.y();
        odom_trans.transform.rotation.z = q.z();
        odom_trans.transform.rotation.w = q.w();

        tf_broadcaster_->sendTransform(odom_trans);

        // 5. Đóng gói dữ liệu và Publish lên Topic /odom
        auto odom_msg = nav_msgs::msg::Odometry();
        odom_msg.header.stamp = current_time;
        odom_msg.header.frame_id = "odom";
        odom_msg.child_frame_id = "base_link";

        // Thiết lập Vị trí (Pose)
        odom_msg.pose.pose.position.x = x_;
        odom_msg.pose.pose.position.y = y_;
        odom_msg.pose.pose.position.z = 0.0;
        odom_msg.pose.pose.orientation.x = q.x();
        odom_msg.pose.pose.orientation.y = q.y();
        odom_msg.pose.pose.orientation.z = q.z();
        odom_msg.pose.pose.orientation.w = q.w();

        // Thiết lập Vận tốc (Twist)
        odom_msg.twist.twist.linear.x = v_linear;
        odom_msg.twist.twist.angular.z = v_angular;

        // Đẩy lên mạng ROS 2
        odom_pub_->publish(odom_msg);
    }

    void readSerialLoop() {
        uint8_t buffer[sizeof(SerialFeedback)];
        size_t byte_count = 0;

        while (rclcpp::ok()) {
            uint8_t c;
            if (read(serial_fd_, &c, 1) > 0) {
                buffer[byte_count] = c;

                if (byte_count == 0 && buffer[0] != (START_FRAME & 0xFF)) continue;
                if (byte_count == 1 && buffer[1] != ((START_FRAME >> 8) & 0xFF)) {
                    byte_count = 0;
                    continue;
                }

                byte_count++;

                if (byte_count >= sizeof(SerialFeedback)) {
                    SerialFeedback* feedback_msg = reinterpret_cast<SerialFeedback*>(buffer);
                    
                    uint16_t calc_checksum = feedback_msg->start ^ feedback_msg->cmd1 ^ feedback_msg->cmd2 ^ 
                                             feedback_msg->speedR_meas ^ feedback_msg->speedL_meas ^ 
                                             feedback_msg->batVoltage ^ feedback_msg->boardTemp ^ feedback_msg->cmdLed; 
                                           

                    if (calc_checksum == feedback_msg->checksum) {
                        // Publish điện áp pin lên hệ thống
                      //  RCLCPP_INFO(this->get_logger(), "Got feedback!");
                        auto bat_msg = std_msgs::msg::Float32();
                        bat_msg.data = feedback_msg->batVoltage / 100.0;
                        battery_pub_->publish(bat_msg);

                        // Xử lý dữ liệu vận tốc bánh xe và đẩy lên /odom & TF
                        processOdometry(feedback_msg->speedR_meas, feedback_msg->speedL_meas);
                    }
                    
                    byte_count = 0;
                }
            } else {
                std::this_thread::sleep_for(1ms);
            }
        }
    }

    int serial_fd_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr battery_pub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    
    rclcpp::TimerBase::SharedPtr write_timer_;
    std::thread read_thread_;
    std::mutex mutex_;

    int16_t raw_speed_ = 0;
    int16_t raw_steer_ = 0;

    // Các thông số cơ khí cấu hình
    double wheel_radius_;
    double wheel_separation_;
    double ticks_per_meter_;

    // Các biến lưu trữ trạng thái vị trí tích phân tích lũy
    double x_ = 0.0;
    double y_ = 0.0;
    double th_ = 0.0;
    rclcpp::Time last_time_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<HoverboardNode>());
    rclcpp::shutdown();
    return 0;
}
