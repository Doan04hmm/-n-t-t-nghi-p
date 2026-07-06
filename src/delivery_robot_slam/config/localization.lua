include "map_builder.lua"
include "trajectory_builder.lua"

MAP_BUILDER.use_trajectory_builder_2d = true

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "odom",
  odom_frame = "odom",

  provide_odom_frame = false,
  publish_frame_projected_to_2d = true,

  use_odometry = true, -- Vẫn giữ bật để lấy mốc thời gian, nhưng ta ép thuật toán lờ nó đi ở bên dưới
  use_nav_sat = false,
  use_landmarks = false,

  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,

  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,

  rangefinder_sampling_ratio = 1.0,
  odometry_sampling_ratio = 1.0,
  fixed_frame_pose_sampling_ratio = 1.0,
  imu_sampling_ratio = 1.0,
  landmarks_sampling_ratio = 1.0,
}

----------------------------------------------------
-- Trajectory Builder 2D (Tập trung toàn lực vào LiDAR)
----------------------------------------------------
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

-- 1. GIỮ CỬA SỔ QUET RỘNG (20 độ): 
-- Giúp LiDAR tự tìm đường và sửa sai khi Odometry báo sai hướng lúc xoay xe.
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.5
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(40.0)

-- 2. ÉP THUẬT TOÁN GIẢM TIN TƯỞNG ODOMETRY:
-- Hạ rotation_weight xuống rất thấp (1.0). Khi xoay xe, Cartographer sẽ ưu tiên 
-- kết quả khớp tia quét của LiDAR thay vì tin vào dữ liệu xoay bị lỗi của bánh xe.

TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 1.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 1.0

-- 3. GIẢM KÍCH THƯỚC SUBMAP (Tối ưu định vị cục bộ):
-- Giảm xuống 20 giúp các submap cục bộ mỏng hơn, load nhanh hơn khi định vị.
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 90

----------------------------------------------------
-- Motion Filter (Cân bằng tần suất chốt vị trí)
----------------------------------------------------
-- Cấu hình cứ xoay 1.0 độ tạo 1 node giúp LiDAR bám đuổi kịp tốc độ quay thực tế 
-- khi không có odom chuẩn hỗ trợ.
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.5
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(10.0)
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 5.0

----------------------------------------------------
-- Pose Graph (Tối ưu hóa đồ thị)
----------------------------------------------------
-- Đặt bằng 20 để giữ chu kỳ tối ưu vừa phải, tránh làm nặng CPU của máy tính.
POSE_GRAPH.optimize_every_n_nodes = 90

-- ĐÃ XÓA TOÀN BỘ CÁC DÒNG MAX_NUM_ITERATIONS LỖI Ở ĐÂY 
-- Hệ thống sẽ tự dùng cấu hình mặc định an toàn của Cartographer.

----------------------------------------------------
-- Pure localization (Thuần định vị)
----------------------------------------------------
TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 3,
}

return options