#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nexus_interfaces.msg import RobotState
VALID={'IDLE','RECEIVED','SEARCHING','PLANNING','MOVING','GRIPPING','DRAWING','VERIFYING','RETURNING','DONE','ERROR'}
class RobotStateManager(Node):
    def __init__(self): super().__init__('robot_state_manager'); self.state='IDLE'; self.create_subscription(RobotState,'/robot/state',self.on_state,10)
    def on_state(self,msg):
        if msg.state in VALID: self.state=msg.state
        self.get_logger().info(f'robot_state={self.state} instruction={msg.instruction_id} detail={msg.detail}')
def main(): rclpy.init(); rclpy.spin(RobotStateManager()); rclpy.shutdown()
