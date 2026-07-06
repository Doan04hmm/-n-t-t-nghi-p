import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    
    # Khai báo đường dẫn cố định tới file YAML
    bt_config_arg = DeclareLaunchArgument(
        'bt_config',
        default_value='/home/nhom3/delivery_robot_ws/src/delivery_robot_navigation/config/bt_navigator_params.yaml',
        description='Path to BT Navigator config file'
    )

    # Khởi chạy node BT Navigator
    bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[LaunchConfiguration('bt_config')]
    )

    # Khởi chạy bộ quản lý vòng đời (Lifecycle Manager)
    lifecycle_mgr_bt = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_bt',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'autostart': True},
            {'node_names': ['bt_navigator']}
        ]
    )

    return LaunchDescription([
        bt_config_arg,
        bt_navigator_node,
        lifecycle_mgr_bt
    ])