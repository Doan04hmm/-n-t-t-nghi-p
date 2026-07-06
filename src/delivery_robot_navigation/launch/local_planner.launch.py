import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    
    controller_config_arg = DeclareLaunchArgument(
        'controller_config',
        default_value='/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/config/nav2_params.yaml', # Đường dẫn tới file cấu hình của bạn
        description='Full path to local planner config file'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false'
    )

    # Node tính toán vận tốc thực tế (Lái robot)
    nav2_controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[
            LaunchConfiguration('controller_config'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    # Lifecycle Manager riêng cho Local Planner
    lifecycle_mgr_controller = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_controller',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'autostart': True},
            {'node_names': ['controller_server']}
        ]
    )

    return LaunchDescription([
        controller_config_arg,
        use_sim_time_arg,
        nav2_controller,
        lifecycle_mgr_controller
    ])