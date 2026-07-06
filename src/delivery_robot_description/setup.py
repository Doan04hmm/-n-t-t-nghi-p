from setuptools import setup
import os
from glob import glob

package_name = 'delivery_robot_description' # Thay tên package của bạn vào đây

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        # Cấu hình để ROS 2 nhận biết package.xml
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # Cấu hình để đưa các thư mục launch, urdf, meshes vào thư mục install
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'meshes'), glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@todo.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)