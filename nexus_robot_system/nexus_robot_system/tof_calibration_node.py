#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from nexus_robot_system.msg import ToFCalibration

class ToFCalibrationNode(Node):
    def __init__(self):
        super().__init__("tof_calibration_node")
        self.declare_parameter("reference_distance_m", 0.10)
        self.create_subscription(Range, "/tof/range", self._on_range, 10)
        self.pub = self.create_publisher(ToFCalibration, "/tof/calibration", 10)
    def _on_range(self, msg):
        ref = float(self.get_parameter("reference_distance_m").value)
        out = ToFCalibration()
        out.header = msg.header
        out.distance_m = msg.range
        out.offset_m = ref - msg.range
        out.calibrated = abs(out.offset_m) < 0.01
        out.status = "calibrated" if out.calibrated else "adjust_sensor_offset"
        self.pub.publish(out)

def main():
    rclpy.init(); rclpy.spin(ToFCalibrationNode()); rclpy.shutdown()
if __name__ == "__main__": main()
