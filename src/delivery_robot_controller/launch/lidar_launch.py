from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    
    # 1. Node LiDAR
    sllidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        parameters=[{
           'serial_port': '/dev/lidar_port',
           'serial_baudrate': 115200,
           'frame_id': 'laser_frame',
            'angle_compensate': True,
            'scan_mode': 'Standard'
        }],
       output='screen'
    )

    # 2. Node Bridge điều khiển Hoverboard (Giả sử nằm trong package 'axioma_bringup')
    # Bạn hãy thay thế 'axioma_bringup' bằng tên package thực tế chứa file hoverboard_bridge.py của bạn.
    # Đảm bảo file python này đã được khai báo entry_point trong setup.py với tên executable là 'hoverboard_bridge'
   # hoverboard_bridge_node = Node(
    #    package='delivery_robot_controller',  # Thay bằng tên package của bạn
    #    executable='hoverboard_bridge.py',
    #    name='hoverboard_bridge_node',
    #    output='screen'
   # )

    # 3. Node điều khiển bằng bàn phím (teleop_twist_keyboard)
    # Vì node này cần nhận tín hiệu trực tiếp từ bàn phím trên terminal, ta dùng cấu hình "prefix"
    # để ép nó mở ra một cửa sổ terminal mới (xterm) hoặc chạy tương tác trực tiếp.
 #   teleop_keyboard_node = Node(
  #      package='teleop_twist_keyboard',
  #      executable='teleop_twist_keyboard',
  #      name='teleop_twist_keyboard',
  #      output='screen',
  #      prefix='xterm -e', # Mở một terminal mới riêng biệt để bạn gõ phím điều khiển
  #  )

    return LaunchDescription([
        sllidar_node,
     #   hoverboard_bridge_node,
   #     teleop_keyboard_node
    ])