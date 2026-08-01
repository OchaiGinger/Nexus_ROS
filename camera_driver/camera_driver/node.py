#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
class CameraDriver(Node):
    def __init__(self):
        super().__init__('camera_driver'); self.declare_parameter('width',640); self.declare_parameter('height',480); self.pub=self.create_publisher(Image,'/camera/image_raw',10); self.create_timer(0.1,self.publish_blank)
    def publish_blank(self):
        w=int(self.get_parameter('width').value); h=int(self.get_parameter('height').value); msg=Image(); msg.header.stamp=self.get_clock().now().to_msg(); msg.height=h; msg.width=w; msg.encoding='rgb8'; msg.step=w*3; msg.data=bytes(w*h*3); self.pub.publish(msg)
def main(): rclpy.init(); rclpy.spin(CameraDriver()); rclpy.shutdown()
