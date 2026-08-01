#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SpeakerNode(Node):
    def __init__(self):
        super().__init__("speaker_node")
        self.create_subscription(String, "/speaker/say", self._on_say, 10)
    def _on_say(self, msg):
        self.get_logger().info(f"speaker: {msg.data}")

def main():
    rclpy.init(); rclpy.spin(SpeakerNode()); rclpy.shutdown()
if __name__ == "__main__": main()
