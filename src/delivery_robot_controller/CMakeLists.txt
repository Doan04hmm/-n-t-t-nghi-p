cmake_minimum_required(VERSION 3.8)
project(delivery_robot_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies (Tìm kiếm các gói phụ thuộc bắt buộc)
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
# =============================================================================
# CẤU HÌNH BIÊN DỊCH NODE C++
# =============================================================================
# Giả định file C++ của bạn được lưu tại: src/hoverboard_node.cpp
add_executable(hoverboard_node src/hoverboard_node.cpp)

# Khai báo các thư viện phụ thuộc liên kết với file C++
ament_target_dependencies(hoverboard_node
  rclcpp
  std_msgs
  geometry_msgs
  nav_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

# Cài đặt file thực thi C++ sau khi build vào thư mục lib để 'ros2 run' tìm thấy
install(TARGETS hoverboard_node
  DESTINATION lib/${PROJECT_NAME}
)
# =============================================================================

# =============================================================================
# TÀI NGUYÊN PYTHON VÀ LAUNCH FILE
# =============================================================================
# Cài đặt thư mục launch vào thư mục share
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Cài đặt file script Python để ROS 2 có thể thực thi
#install(PROGRAMS
#  src/hoverboard_bridge.py
#  DESTINATION lib/${PROJECT_NAME}
#)
# =============================================================================

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()