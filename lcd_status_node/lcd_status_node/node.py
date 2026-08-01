#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
class LcdStatusNode(Node):
    def __init__(self): super().__init__('lcd_status_node'); self.create_subscription(String,'/lcd/status',self.on_status,10)
    def on_status(self,msg): self.get_logger().info(f'LCD[16x1]: {msg.data[:16]:<16}')
def main(): rclpy.init(); rclpy.spin(LcdStatusNode()); rclpy.shutdown()
