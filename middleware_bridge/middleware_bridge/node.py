#!/usr/bin/env python3
import json, time
from collections import deque
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nexus_interfaces.msg import ActionRequest, ActionDone, RobotState, DiagnosticEvent

REQUIRED = {'instruction_id', 'actor_id', 'action'}
SUPPORTED = {'pick','place','draw','arc','pick_and_place','pick_and_draw','drop_back'}

class MiddlewareBridge(Node):
    def __init__(self):
        super().__init__('middleware_bridge')
        self.declare_parameter('request_timeout_sec', 30.0)
        self.declare_parameter('max_queue_size', 50)
        self.declare_parameter('max_retries', 2)
        self.pending = {}
        self.queue = deque(maxlen=int(self.get_parameter('max_queue_size').value))
        self.create_subscription(String, '/frontend/instructions', self.on_frontend_json, 10)
        self.create_subscription(ActionDone, '/robot/action/done', self.on_done, 10)
        self.req_pub = self.create_publisher(ActionRequest, '/robot/action/request', 10)
        self.done_pub = self.create_publisher(String, '/frontend/action_done', 10)
        self.lcd_pub = self.create_publisher(String, '/lcd/status', 10)
        self.speaker_pub = self.create_publisher(String, '/speaker/say', 10)
        self.state_pub = self.create_publisher(RobotState, '/robot/state', 10)
        self.diag_pub = self.create_publisher(DiagnosticEvent, '/diagnostics/events', 10)
        self.create_timer(0.25, self.pump_queue)
        self.create_timer(1.0, self.check_timeouts)

    def on_frontend_json(self, msg):
        try:
            payload = json.loads(msg.data)
            missing = sorted(REQUIRED - payload.keys())
            if missing: raise ValueError(f'missing required fields: {missing}')
            action = str(payload['action']).lower().replace(' ', '_')
            if action not in SUPPORTED: raise ValueError(f'unsupported action: {action}')
            self.queue.append(payload)
            self.publish_state(payload['instruction_id'], 'RECEIVED', f'queued {action}')
        except Exception as exc:
            self.publish_frontend_done({'instruction_id': '', 'actor_id': '', 'status':'ERROR', 'success':False, 'message':str(exc)})

    def pump_queue(self):
        if not self.queue: return
        payload = self.queue.popleft(); req = ActionRequest()
        req.header.stamp = self.get_clock().now().to_msg(); req.instruction_id = str(payload['instruction_id']); req.actor_id = str(payload['actor_id'])
        req.action = str(payload['action']).lower().replace(' ', '_'); req.tool = str(payload.get('tool','')); req.target = str(payload.get('target',''))
        loc = payload.get('estimated_location') or {}; req.estimated_location.x=float(loc.get('x',0)); req.estimated_location.y=float(loc.get('y',0)); req.estimated_location.z=float(loc.get('z',0))
        req.grid_id = str(payload.get('grid_id','')); req.json_payload = json.dumps(payload); req.max_retries = int(payload.get('max_retries', self.get_parameter('max_retries').value))
        self.pending[req.instruction_id] = {'actor_id':req.actor_id, 'sent':time.monotonic(), 'payload':payload, 'tries':0}
        self.req_pub.publish(req); self.lcd_pub.publish(String(data='Planning')); self.speaker_pub.publish(String(data=f'Received {req.action}'))
        self.publish_state(req.instruction_id, 'RECEIVED', 'published ActionRequest')

    def on_done(self, done):
        self.pending.pop(done.instruction_id, None)
        status = 'DONE' if done.success else 'ERROR'
        self.lcd_pub.publish(String(data=status)); self.speaker_pub.publish(String(data=done.message or status))
        self.publish_frontend_done({'instruction_id':done.instruction_id,'actor_id':done.actor_id,'status':status,'success':bool(done.success),'message':done.message})
        self.publish_state(done.instruction_id, status, done.message)

    def check_timeouts(self):
        timeout = float(self.get_parameter('request_timeout_sec').value); now=time.monotonic()
        for iid, item in list(self.pending.items()):
            if now - item['sent'] > timeout:
                self.pending.pop(iid, None)
                self.publish_frontend_done({'instruction_id':iid,'actor_id':item['actor_id'],'status':'ERROR','success':False,'message':'execution timeout'})
                self.publish_state(iid, 'ERROR', 'execution timeout')

    def publish_frontend_done(self, payload): self.done_pub.publish(String(data=json.dumps(payload)))
    def publish_state(self, iid, state, detail):
        msg=RobotState(); msg.header.stamp=self.get_clock().now().to_msg(); msg.instruction_id=str(iid); msg.state=state; msg.detail=detail; self.state_pub.publish(msg)

def main():
    rclpy.init(); rclpy.spin(MiddlewareBridge()); rclpy.shutdown()
