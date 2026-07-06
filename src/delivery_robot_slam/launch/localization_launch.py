from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Đường dẫn file pbstream của bạn
    pbstream_file = '/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/maps/map_lab.pbstream' # Thay bằng đường dẫn của bạn
    config_dir = '/home/nhom3/delivery_robot_ws/src/delivery_robot_slam/config' # Thay bằng đường dẫn tới thư mục chứa file .lua

    return LaunchDescription([
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=[
                '-configuration_directory', config_dir,
                '-configuration_basename', 'localization.lua',
                '-load_state_filename', pbstream_file
            ],
           # remappings=[
           #     ('/scan', 'scan'),
           #     ('/odom', 'odom')
           # ]
        ),
        # Node phát bản đồ (nếu cần hiển thị lên RViz để so khớp)
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=['-resolution', '0.05']
        )
    ])
