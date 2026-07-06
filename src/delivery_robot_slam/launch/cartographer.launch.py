import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('delivery_robot_slam')
    
    # Đường dẫn file cấu hình
    configuration_directory = os.path.join(pkg_share, 'config')
    configuration_basename = 'delivery_robot.lua'

    return LaunchDescription([
        # 1. Node Cartographer chính
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=[
                '-configuration_directory', configuration_directory,
                '-configuration_basename', configuration_basename
            ],
           
        ),

        # 2. Node tạo Occupancy Grid (để hiện bản đồ đen trắng trên Rviz)
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
        ),
        
        # 3. Static TF (Quan trọng: Khai báo LiDAR nằm ở đâu so với robot)
        # Giả sử LiDAR nằm cao hơn tâm robot 15cm
       # Node(
       #     package='tf2_ros',
       #     executable='static_transform_publisher',
       #     arguments=['0', '0', '0.15', '0', '0', '0', 'base_link', 'laser_frame']
       # ),
    ])