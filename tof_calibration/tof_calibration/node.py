#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from nexus_interfaces.msg import ToFCalibration
from nexus_interfaces.srv import CalibrateToF
class ToFCalibrationNode(Node):
    def __init__(self):
        super().__init__('tof_calibration'); self.declare_parameter('workspace_z_m',0.0); self.reference=0.10; self.last=0.0
        self.create_subscription(Range,'/tof/range',self.on_range,10); self.pub=self.create_publisher(ToFCalibration,'/tof/calibration',10); self.create_service(CalibrateToF,'/tof/calibrate',self.on_calibrate)
    def on_range(self,msg):
        self.last=msg.range; out=ToFCalibration(); out.header=msg.header; out.height_m=msg.range; out.offset_m=self.reference-msg.range; out.workspace_z_m=float(self.get_parameter('workspace_z_m').value)+out.offset_m; out.calibrated=abs(out.offset_m)<0.01; out.status='CALIBRATED' if out.calibrated else 'NEEDS_OFFSET'; self.pub.publish(out)
    def on_calibrate(self,req,res): self.reference=req.reference_height_m; res.success=True; res.offset_m=self.reference-self.last; res.message='reference updated'; return res
def main(): rclpy.init(); rclpy.spin(ToFCalibrationNode()); rclpy.shutdown()
