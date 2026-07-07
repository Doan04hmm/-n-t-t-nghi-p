# datn-delivery-robot-slam-nav2

Bộ tài liệu hỗ trợ triển khai SLAM và Nav2 trên delivery robot, đồng thời tích hợp điều khiển AI vào hệ thống robot.

---

## 1. Yêu cầu hệ điều hành

Các thiết bị sử dụng trong đồ án cần cài đặt hệ điều hành như sau:

| Thiết bị | Hệ điều hành yêu cầu |
|---|---|
| Máy tính chủ | Ubuntu 22.04 LTS |
| Mini ASUS | Ubuntu 22.04 LTS |

---

## 2. Hướng dẫn cài đặt ROS2 Humble trên Ubuntu

Đồ án sử dụng ROS2 phiên bản **Humble**. Các bước cài đặt ROS2 trên các thiết bị sử dụng Ubuntu 22.04 LTS là giống nhau.

### Bước 1: Cập nhật Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
```

### Bước 2: Cài đặt Locale UTF-8

ROS2 cần môi trường UTF-8 để hoạt động ổn định.

```bash
sudo apt update
sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
```

### Bước 3: Bật Repository Universe

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe
```

### Bước 4: Thêm kho ROS2

Cài đặt curl:

```bash
sudo apt install curl -y
```

Tạo key cho ROS2:

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
```

Thêm nguồn ROS2:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list
```

### Bước 5: Cập nhật lại apt

```bash
sudo apt update
```

### Bước 6: Cài đặt ROS2 Humble Desktop

```bash
sudo apt install ros-humble-desktop -y
```

Gói `ros-humble-desktop` bao gồm:

- ROS2 core
- RViz2
- Gazebo
- Các công cụ demo
- Thư viện Python/C++

### Bước 7: Cài đặt công cụ build

```bash
sudo apt install ros-dev-tools -y
sudo apt install python3-colcon-common-extensions -y
```

### Bước 8: Nạp ROS2 vào Terminal

Mỗi lần mở terminal cần source ROS2:

```bash
source /opt/ros/humble/setup.bash
```

Để tự động source mỗi khi mở terminal:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Bước 9: Khởi tạo workspace cho ROS2

Tạo workspace:

```bash
mkdir -p ~/delivery_robot_ws/src
cd ~/delivery_robot_ws
colcon build
```

Nạp workspace:

```bash
source install/setup.bash
```

Để tự động nạp workspace mỗi khi mở terminal:

```bash
echo "source ~/delivery_robot_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Cài đặt các gói cần thiết

### Nav2

```bash
sudo apt install ros-humble-navigation2 -y
sudo apt install ros-humble-nav2-bringup -y
```

### Cartographer

```bash
sudo apt install ros-humble-cartographer -y
sudo apt install ros-humble-cartographer-ros -y
```

### LiDAR

```bash
sudo apt install ros-humble-rplidar-ros -y
```

### Gazebo

```bash
sudo apt install ros-humble-gazebo-ros-pkgs -y
```

### Kiểm tra cài đặt Nav2

```bash
ros2 pkg list | grep nav2
```

---

## 4. Kiểm tra LiDAR

Để kiểm tra LiDAR, chạy lần lượt các lệnh sau trên terminal.

### Kiểm tra cổng kết nối

```bash
ls /dev/tty*
```

Thông thường LiDAR sẽ nhận cổng dạng:

```bash
/dev/ttyUSB0
```

### Cấp quyền cho cổng LiDAR

```bash
sudo chmod 777 /dev/ttyUSB0
```

### Cài đặt package RPLiDAR

```bash
sudo apt install ros-humble-rplidar-ros -y
```

### Kiểm tra package RPLiDAR

```bash
ros2 pkg list | grep rplidar
```

### Chạy node LiDAR

```bash
source /opt/ros/humble/setup.bash
ros2 launch rplidar_ros rplidar.launch.py
```

### Kiểm tra topic

Mở terminal mới và chạy:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
```

### Xem dữ liệu LiDAR

```bash
ros2 topic echo /scan
```

### Hiển thị dữ liệu LiDAR bằng RViz2

Chạy RViz2:

```bash
rviz2
```

Trong RViz2:

1. Đổi `Fixed Frame` thành `laser_frame` hoặc `base_link`.
2. Bấm `Add`.
3. Chọn kiểu hiển thị `LaserScan`.
4. Ở mục `Topic`, chọn `/scan`.

---

## 5. Link code GitHub

Các package và mã nguồn dùng để chạy LiDAR, Cartographer và Nav2 được đặt trong workspace:

```bash
~/delivery_robot_ws/src
```

Link repository:

```text
https://github.com/Doan04hmm/-n-t-t-nghi-p
```

---

## 6. Nội dung chính của repository

Repository này bao gồm tài liệu và mã nguồn phục vụ cho các nội dung chính:

- Cài đặt ROS2 Humble trên Ubuntu 22.04 LTS
- Kiểm tra và chạy LiDAR
- Triển khai SLAM bằng Cartographer
- Triển khai điều hướng robot bằng Nav2
- Hỗ trợ tích hợp điều khiển AI cho delivery robot

  # Hướng dẫn sử dụng Delivery Robot (ROS 2)

## Tổng hợp câu lệnh

```bash
# (1) Hiển thị mô hình robot
ros2 launch delivery_robot_description display.launch.py

# (2) Chạy SLAM Cartographer
ros2 launch delivery_robot_bringup delivery_robot_slam_bringup

# (3) Chạy Navigation2
ros2 launch delivery_robot_navigation nav2_bringup.launch.py

# (4) Localization
ros2 launch delivery_robot_slam localization_launch.py

# (5) Khởi động Navigation Bringup
ros2 launch delivery_robot_bringup delivery_robot_nav_bringup

# (6) Kết nối bộ điều khiển robot
ros2 launch delivery_robot_controller delivery_control_launch.py

# (7) Lưu bản đồ Cartographer
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
"{filename: '/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/maps/map_final.pbstream'}"

# (8) Chạy chương trình điều khiển AI
ros2 run delivery_robot_ai dieu_khien.py

# (9) Giao diện khuôn mặt robot
ros2 run delivery_robot_ai robot_face_node.py
```

> **Lưu ý:** Chạy lệnh **(9)** nếu muốn hiển thị giao diện khuôn mặt của robot.

---

# 1. Chạy Navigation

## Bước 1: Chọn bản đồ

Mở file:

```text
/home/delivery_robot_ws/src/delivery_robot_slam/launch/localization_launch.py
```

Tìm dòng chứa:

```python
map_lab.pbstream
```

Đổi thành:

```python
map_hl.pbstream
```

Lưu file, sau đó mở Terminal mới và build lại:

```bash
cd ~/delivery_robot_ws
colcon build
```

---

## Bước 2

Mở Terminal mới:

```bash
cd ~/delivery_robot_ws
```

---

## Bước 3

Chạy lệnh **(6)**:

```bash
ros2 launch delivery_robot_controller delivery_control_launch.py
```

Kiểm tra Terminal:

- Đã kết nối **động cơ**
- Đã kết nối **LiDAR**

Nếu lỗi:

1. Nhấn **Ctrl + C**
2. Rút dây LiDAR
3. Cắm lại
4. Chạy lại lệnh.

---

## Bước 4

Mở Terminal mới và chạy:

```bash
ros2 launch delivery_robot_bringup delivery_robot_nav_bringup
```

**Lưu ý**

- Không đứng chắn trước LiDAR trong lúc khởi động.

---

## Bước 5

Mở Terminal mới:

```bash
ros2 run delivery_robot_ai dieu_khien.py
```

---

## Bước 6

Sử dụng điện thoại để gửi lệnh điều khiển robot.

---

### Dừng chương trình

Nhấn:

```text
Ctrl + C
```

---

# 2. Lấy tọa độ và gán vào chương trình điều khiển

## Bước 1

```bash
cd ~/delivery_robot_ws
```

---

## Bước 2

Chạy:

```bash
ros2 launch delivery_robot_controller delivery_control_launch.py
```

Kiểm tra đã kết nối:

- Động cơ
- LiDAR

Nếu lỗi:

- Ctrl + C
- Rút và cắm lại LiDAR
- Chạy lại.

---

## Bước 3

Chạy:

```bash
ros2 launch delivery_robot_bringup delivery_robot_nav_bringup
```

Không đứng chắn trước LiDAR.

---

## Bước 4

Trong RViz:

- Chọn **2D Goal Pose**
- Chọn một điểm trên bản đồ
- Kéo theo hướng robot muốn quay.

---

## Bước 5

Mở Terminal mới để đọc tọa độ vừa chọn.

> *(Chạy node hoặc lệnh đang dùng để hiển thị Goal Pose.)*

---

## Bước 6

Mở file:

```text
/home/delivery_robot_ws/src/delivery_robot_ai/src/dieukhien.py
```

Tìm các tọa độ:

- A
- B
- C

Thay bằng tọa độ mới.

Sau đó:

```bash
cd ~/delivery_robot_ws
colcon build
```

Build lại workspace.

---


# 3. Chạy SLAM Cartographer

## Bước 1

```bash
cd ~/delivery_robot_ws
```

---

## Bước 2

Chạy:

```bash
ros2 launch delivery_robot_bringup delivery_robot_slam_bringup
```

---

## Bước 3

Lưu bản đồ:

```bash
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
"{filename: '/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/maps/map_final.pbstream'}"
```

Map sẽ được lưu với tên:

```text
map_final.pbstream
```
