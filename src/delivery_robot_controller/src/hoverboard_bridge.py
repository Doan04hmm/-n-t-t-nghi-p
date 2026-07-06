#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

class HoverboardBridge(Node):
    def __init__(self):
        super().__init__('hoverboard_bridge')
        
        # Cấu hình cổng Serial kết nối với Arduino (Thay đổi đúng cổng của bạn)
        # Trên Linux thường là '/dev/ttyUSB0' hoặc '/dev/ttyACM0'
        try:
            self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=0.1)
            self.get_logger().info("Đã kết nối thành công với Arduino!")
        except Exception as e:
            self.get_logger().error(f"Không thể kết nối cổng Serial: {e}")

        # Subscribe topic /cmd_vel từ teleop_keyboard
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
        
        # Hệ số quy đổi từ m/s và rad/s sang đơn vị [-1000, 1000] của Hoverboard
        # Bạn cần tinh chỉnh lại 2 hệ số này sau khi chạy thử
        self.SPEED_SCALE = 3.3  
        self.STEER_SCALE = 400.0

    def cmd_vel_callback(self, msg):
        # Lấy vận tốc tuyến tính x (tiến/lùi) và vận tốc góc z (xoay)
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        # Quy đổi sang giá trị Hoverboard hiểu (ép kiểu về số nguyên)
        speed = int(linear_x * self.SPEED_SCALE)
        steer = int(angular_z * self.STEER_SCALE)

        # Giới hạn trong khoảng [-1000, 1000] để an toàn
        speed = max(min(speed, 1000), -1000)
        steer = max(min(steer, 1000), -1000)

        # Định dạng chuỗi dữ liệu "speed,steer\n"
        packet = f"{speed},{steer}\n"
        
        # Gửi xuống Arduino qua USB
        if hasattr(self, 'arduino') and self.arduino.is_open:
            self.arduino.write(packet.encode('utf-8'))
            self.get_logger().info(f"Đã gửi: Speed={speed}, Steer={steer}")

def main(args=None):
    rclpy.init(args=args)
    node = HoverboardBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(node, 'arduino'):
            node.arduino.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
    