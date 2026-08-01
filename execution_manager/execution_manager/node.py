#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nexus_interfaces.msg import ActionRequest, ActionDone, PerceptionContext, GridDetectionArray, RobotState

class Routine:
    steps=[]
    def __init__(self,node,req): self.node=node; self.req=req
    def run(self):
        retries=0
        for step, mode in self.steps:
            self.node.set_state(self.req.instruction_id, self.state_for(step), step)
            if mode: self.node.set_perception(self.req, mode)
            ok = self.node.call_motion_step(self.req, step)
            while not ok and retries < self.req.max_retries:
                retries += 1; ok = self.node.call_motion_step(self.req, step)
            if not ok: return False, retries, f'{step} failed'
        return True, retries, f'{self.req.action} complete'
    def state_for(self,step):
        if 'grip' in step: return 'GRIPPING'
        if 'draw' in step or 'trace' in step: return 'DRAWING'
        if 'verify' in step: return 'VERIFYING'
        if 'return' in step or 'home' in step: return 'RETURNING'
        return 'MOVING'
class PickRoutine(Routine): steps=[('search_tool','SEARCH_TOOL'),('pick_motion',None),('verify_pick','VERIFY_PICK')]
class PlaceRoutine(Routine): steps=[('search_target','SEARCH_PAPER'),('place_motion',None),('verify_place','VERIFY_PLACE')]
class DrawRoutine(Routine): steps=[('search_paper','SEARCH_PAPER'),('draw_grid','DRAW_GRID'),('draw_motion',None)]
class ArcRoutine(Routine): steps=[('search_paper','SEARCH_PAPER'),('draw_grid','DRAW_GRID'),('arc_motion',None)]
class PickPlaceRoutine(Routine): steps=PickRoutine.steps + PlaceRoutine.steps
class PickDrawRoutine(Routine): steps=PickRoutine.steps + DrawRoutine.steps + [('return_tool','SEARCH_TOOL'),('verify_place','VERIFY_PLACE')]
class DropBackRoutine(Routine): steps=[('return_tool','SEARCH_TOOL'),('drop_back_motion',None),('home',None)]
ROUTINES={'pick':PickRoutine,'place':PlaceRoutine,'draw':DrawRoutine,'arc':ArcRoutine,'pick_and_place':PickPlaceRoutine,'pick_and_draw':PickDrawRoutine,'drop_back':DropBackRoutine}
class ExecutionManager(Node):
    def __init__(self):
        super().__init__('execution_manager'); self.latest_grid=GridDetectionArray()
        self.create_subscription(ActionRequest,'/robot/action/request',self.on_request,10); self.create_subscription(GridDetectionArray,'/perception/grid_detections',lambda m:setattr(self,'latest_grid',m),10)
        self.context_pub=self.create_publisher(PerceptionContext,'/perception/context',10); self.done_pub=self.create_publisher(ActionDone,'/robot/action/done',10); self.motion_pub=self.create_publisher(String,'/motion/plan_request',10); self.state_pub=self.create_publisher(RobotState,'/robot/state',10); self.lcd_pub=self.create_publisher(String,'/lcd/status',10)
    def on_request(self,req):
        cls=ROUTINES.get(req.action); self.set_state(req.instruction_id,'PLANNING',req.action); self.lcd_pub.publish(String(data='Planning'))
        if not cls: return self.done(req,False,0,'unsupported action')
        success,retries,msg=cls(self,req).run(); self.done(req,success,retries,msg)
    def set_perception(self,req,mode):
        msg=PerceptionContext(); msg.header.stamp=self.get_clock().now().to_msg(); msg.instruction_id=req.instruction_id; msg.mode=mode; msg.priority_label=req.tool or req.target; msg.target_grid_id=req.grid_id; self.context_pub.publish(msg)
    def call_motion_step(self,req,step):
        self.motion_pub.publish(String(data=f'{req.instruction_id}:{step}:{req.grid_id}')); time.sleep(0.02); return True
    def set_state(self,iid,state,detail):
        s=RobotState(); s.header.stamp=self.get_clock().now().to_msg(); s.instruction_id=iid; s.state=state; s.detail=detail; self.state_pub.publish(s); self.lcd_pub.publish(String(data=state[:16]))
    def done(self,req,success,retries,message):
        d=ActionDone(); d.header.stamp=self.get_clock().now().to_msg(); d.instruction_id=req.instruction_id; d.actor_id=req.actor_id; d.status='DONE' if success else 'ERROR'; d.success=success; d.message=message; d.retry_count=retries; self.done_pub.publish(d); self.set_state(req.instruction_id,d.status,message)
def main(): rclpy.init(); rclpy.spin(ExecutionManager()); rclpy.shutdown()
