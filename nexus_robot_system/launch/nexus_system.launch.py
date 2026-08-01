from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def generate_launch_description():
    share = Path(get_package_share_directory("nexus_robot_system"))
    grid_config = str(share / "config" / "grid_perception.yaml")
    return LaunchDescription([
        Node(package="nexus_robot_system", executable="middleware_bridge.py", name="middleware_bridge"),
        Node(package="nexus_robot_system", executable="moveit_action_executor.py", name="moveit_action_executor"),
        Node(package="nexus_robot_system", executable="yolo_grid_perception.py", name="yolo_grid_perception", parameters=[grid_config]),
        Node(package="nexus_robot_system", executable="tof_calibration_node.py", name="tof_calibration_node"),
        Node(package="nexus_robot_system", executable="lcd_status_node.py", name="lcd_status_node"),
        Node(package="nexus_robot_system", executable="speaker_node.py", name="speaker_node"),
    ])
