from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='camera_driver', executable='camera_driver'),
        Node(package='middleware_bridge', executable='middleware_bridge'),
        Node(package='execution_manager', executable='execution_manager'),
        Node(package='perception_manager', executable='perception_manager'),
        Node(package='yolo_grid_perception', executable='yolo_grid_perception'),
        Node(package='tof_calibration', executable='tof_calibration'),
        Node(package='moveit_motion_controller', executable='moveit_motion_controller'),
        Node(package='stepper_driver', executable='stepper_driver'),
        Node(package='lcd_status_node', executable='lcd_status_node'),
        Node(package='speaker_node', executable='speaker_node'),
        Node(package='robot_state_manager', executable='robot_state_manager'),
        Node(package='diagnostics_logger', executable='diagnostics_logger'),
    ])
