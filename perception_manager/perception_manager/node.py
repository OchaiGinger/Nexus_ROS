#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nexus_interfaces.msg import PerceptionContext, RobotState
VALID={'IDLE','SEARCH_TOOL','TRACK_TOOL','SEARCH_PAPER','TRACK_PAPER','VERIFY_PICK','VERIFY_PLACE','DRAW_GRID'}
class PerceptionManager(Node):
    def __init__(self):
        super().__init__('perception_manager'); self.mode='IDLE'
        self.create_subscription(PerceptionContext,'/perception/context',self.on_context,10)
        self.state_pub=self.create_publisher(RobotState,'/robot/state',10)
    def on_context(self,msg):
        self.mode = msg.mode if msg.mode in VALID else 'IDLE'
        s=RobotState(); s.header.stamp=self.get_clock().now().to_msg(); s.instruction_id=msg.instruction_id; s.state='SEARCHING' if 'SEARCH' in self.mode else 'VERIFYING' if 'VERIFY' in self.mode else 'IDLE'; s.detail=f'perception mode {self.mode} priority={msg.priority_label}'
        self.state_pub.publish(s)
def main(): rclpy.init(); rclpy.spin(PerceptionManager()); rclpy.shutdown()
