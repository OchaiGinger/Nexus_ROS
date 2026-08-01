#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
class SpeakerNode(Node):
    def __init__(self): super().__init__('speaker_node'); self.create_subscription(String,'/speaker/say',self.on_say,10)
    def on_say(self,msg): self.get_logger().info(f'speaker says: {msg.data}')
def main(): rclpy.init(); rclpy.spin(SpeakerNode()); rclpy.shutdown()
