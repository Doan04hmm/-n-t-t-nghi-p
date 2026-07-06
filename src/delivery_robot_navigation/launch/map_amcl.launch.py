import os
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    my_pkg_dir = get_package_share_directory('delivery_robot_navigation')
    map_file = os.path.join(my_pkg_dir, 'maps', 'my_map3.yaml') 
    
    # 1. Khởi tạo LaunchConfigurations
    use_sim_time = LaunchConfiguration("use_sim_time")
    amcl_config = LaunchConfiguration("amcl_config")
    map_yaml = LaunchConfiguration('map', default=map_file)
    
    lifecycle_nodes = ["map_server", "amcl"]

    # 2. Khai báo LaunchArguments (Đã gán biến map_arg)
    map_arg = DeclareLaunchArgument(
        'map', 
        default_value=map_file, 
        description='Full path to map yaml file'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true"
    )

    amcl_config_arg = DeclareLaunchArgument(
        "amcl_config",
        default_value=os.path.join(
            my_pkg_dir,
            "config",
            "nav2_params.yaml"
        ),
        description="Full path to amcl yaml file to load"
    )

    # 3. Cấu hình các Nodes
    nav2_map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {"yaml_filename": map_yaml},
            {"use_sim_time": use_sim_time}
        ],
    )

    nav2_amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        emulate_tty=True,
        parameters=[
            amcl_config, # Chú ý: Ở đây bạn đang truyền trực tiếp chuỗi yaml vào config. Hãy đảm bảo nav2_params.yaml chứa cấu hình đúng chuẩn Nav2.
            {"use_sim_time": use_sim_time},
        ],
    )

    nav2_lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {"node_names": lifecycle_nodes},
            {"use_sim_time": use_sim_time},
            {"autostart": True}
        ],
    )

    # 4. Trả về LaunchDescription đầy đủ
    return LaunchDescription([
        map_arg,             
        use_sim_time_arg,
        amcl_config_arg,
        nav2_map_server,
        nav2_amcl,
        nav2_lifecycle_manager,
    ])