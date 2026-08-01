cmake_minimum_required(VERSION 3.8)
project(nexus_interfaces)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ActionRequest.msg" "msg/ActionDone.msg" "msg/GridDetection.msg" "msg/GridDetectionArray.msg"
  "msg/RobotState.msg" "msg/PerceptionContext.msg" "msg/ToFCalibration.msg" "msg/DiagnosticEvent.msg"
  "action/MotionPlan.action" "srv/CalibrateToF.srv"
  DEPENDENCIES std_msgs geometry_msgs trajectory_msgs builtin_interfaces)
ament_package()
