#!/usr/bin/env python3
import csv, time
import rclpy
from rclpy.node import Node
from nexus_interfaces.msg import DiagnosticEvent, RobotState, ActionDone
class DiagnosticsLogger(Node):
    def __init__(self):
        super().__init__('diagnostics_logger'); self.declare_parameter('log_path','/tmp/nexus_diagnostics.csv'); self.started={}
        self.create_subscription(DiagnosticEvent,'/diagnostics/events',self.on_event,10); self.create_subscription(RobotState,'/robot/state',self.on_state,10); self.create_subscription(ActionDone,'/robot/action/done',self.on_done,10)
    def write(self,row):
        with open(str(self.get_parameter('log_path').value),'a',newline='') as f: csv.writer(f).writerow(row)
    def on_event(self,msg): self.write([time.time(),msg.instruction_id,msg.actor_id,msg.node_name,msg.event,msg.duration_ms,msg.retry_count,msg.message])
    def on_state(self,msg):
        if msg.state=='RECEIVED': self.started[msg.instruction_id]=time.monotonic()
        self.write([time.time(),msg.instruction_id,'','robot_state_manager',msg.state,0,0,msg.detail])
    def on_done(self,msg): self.write([time.time(),msg.instruction_id,msg.actor_id,'execution',msg.status,(time.monotonic()-self.started.get(msg.instruction_id,time.monotonic()))*1000,msg.retry_count,msg.message])
def main(): rclpy.init(); rclpy.spin(DiagnosticsLogger()); rclpy.shutdown()
