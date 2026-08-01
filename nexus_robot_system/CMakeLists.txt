cmake_minimum_required(VERSION 3.8)
project(nexus_robot_system)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/FrontendInstruction.msg"
  "msg/ActionRequest.msg"
  "msg/ActionDone.msg"
  "msg/GridDetection.msg"
  "msg/GridDetectionArray.msg"
  "msg/ToFCalibration.msg"
  DEPENDENCIES std_msgs sensor_msgs geometry_msgs builtin_interfaces
)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  nexus_robot_system/middleware_bridge.py
  nexus_robot_system/moveit_action_executor.py
  nexus_robot_system/yolo_grid_perception.py
  nexus_robot_system/tof_calibration_node.py
  nexus_robot_system/lcd_status_node.py
  nexus_robot_system/speaker_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
