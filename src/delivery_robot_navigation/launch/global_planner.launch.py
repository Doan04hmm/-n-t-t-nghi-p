import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    
    planner_config_arg = DeclareLaunchArgument(
        'planner_config',
        default_value='/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/config/nav2_params.yaml', # Đường dẫn tới file cấu hình của bạn
        description='Full path to global planner config file'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false'
    )

    # Node vẽ đường đi tổng thể
    nav2_planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[
            LaunchConfiguration('planner_config'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    # Lifecycle Manager riêng cho Global Planner
    lifecycle_mgr_planner = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_planner',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'autostart': True},
            {'node_names': ['planner_server']} 
        ]
    )

    return LaunchDescription([
        planner_config_arg,
        use_sim_time_arg,
        nav2_planner,
        lifecycle_mgr_planner
    ])