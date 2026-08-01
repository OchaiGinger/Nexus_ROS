#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nexus_interfaces.msg import GridDetection, GridDetectionArray, PerceptionContext, ToFCalibration

class YoloGridPerception(Node):
    def __init__(self):
        super().__init__('yolo_grid_perception')
        self.declare_parameter('rows',12); self.declare_parameter('columns',12); self.declare_parameter('image_width',640.0); self.declare_parameter('image_height',480.0); self.declare_parameter('meters_per_pixel',0.001)
        self.mode='IDLE'; self.priority=''; self.tof_z=0.0; self.frame_count=0
        self.create_subscription(Image,'/camera/image_raw',self.on_image,10); self.create_subscription(PerceptionContext,'/perception/context',self.on_context,10); self.create_subscription(ToFCalibration,'/tof/calibration',self.on_tof,10)
        self.pub=self.create_publisher(GridDetectionArray,'/perception/grid_detections',10); self.create_timer(0.1,self.publish_grid)
    def on_context(self,msg): self.mode=msg.mode; self.priority=msg.priority_label
    def on_tof(self,msg): self.tof_z=msg.workspace_z_m
    def on_image(self,msg): self.frame_count += 1; self.publish_grid(msg.header)
    def publish_grid(self, header=None):
        rows=int(self.get_parameter('rows').value); cols=int(self.get_parameter('columns').value); w=float(self.get_parameter('image_width').value); h=float(self.get_parameter('image_height').value)
        out=GridDetectionArray(); out.header = header if header else out.header; out.header.stamp=self.get_clock().now().to_msg(); out.rows=rows; out.columns=cols; out.active_mode=self.mode; out.paper_visible=self.mode in {'SEARCH_PAPER','TRACK_PAPER','DRAW_GRID'}; out.homography_valid=out.paper_visible
        if self.mode != 'IDLE': out.detections=[self.fake_detection(rows,cols,w,h)]
        self.pub.publish(out)
    def fake_detection(self,rows,cols,w,h):
        label = self.priority or ('paper' if 'PAPER' in self.mode or self.mode=='DRAW_GRID' else 'tool')
        x=w*0.64; y=h*0.27; cell_w=w/cols; cell_h=h/rows; col=max(0,min(cols-1,int(x//cell_w))); row=max(0,min(rows-1,int(y//cell_h)))
        d=GridDetection(); d.header.stamp=self.get_clock().now().to_msg(); d.object_id=f'{label}-{self.frame_count}'; d.label=label; d.grid_id=f'R{row+1}C{col+1}'; d.center_px.x=x; d.center_px.y=y; d.robot_pose.position.x=x*float(self.get_parameter('meters_per_pixel').value); d.robot_pose.position.y=y*float(self.get_parameter('meters_per_pixel').value); d.robot_pose.position.z=self.tof_z; d.robot_pose.orientation.w=1.0; d.confidence=0.90; d.rotation_rad=0.0; d.virtual_line_offset_px=x-(w/2.0); d.virtual_line_offset_m=abs(d.virtual_line_offset_px)*float(self.get_parameter('meters_per_pixel').value); d.stable=True
        return d
def main(): rclpy.init(); rclpy.spin(YoloGridPerception()); rclpy.shutdown()
