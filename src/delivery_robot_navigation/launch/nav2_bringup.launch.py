from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    my_pkg_dir = get_package_share_directory('delivery_robot_navigation')

    #map_file = os.path.join(my_pkg_dir, 'maps', 'my_map3.yaml') 
    params_file = os.path.join(my_pkg_dir, 'config', 'nav2_params.yaml')
    #DeclareLaunchArgument('map', default_value=map_file, description='Full path to map yaml file')
    #map_yaml = LaunchConfiguration('map', default=map_file)
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    nav2_bringup_dir,
                    'launch',
                    'navigation_launch.py'
                )
            ),
            launch_arguments={
                #'map': map_yaml,
                'params_file': params_file,
                'use_sim_time': 'false'
            }.items()
        )
    ])