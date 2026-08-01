#!/usr/bin/env python3
"""Bridge frontend JSON instructions to ROS action topics and route completion events."""
import json
from typing import Any, Dict

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from std_msgs.msg import String

from nexus_robot_system.msg import ActionDone, ActionRequest, FrontendInstruction

SUPPORTED_ACTIONS = {"draw", "pick", "place", "arc", "pick_and_place", "pick_and_draw", "drop_back"}


class MiddlewareBridge(Node):
    """Receives Next.js actor instructions, dispatches ROS requests, and returns done events."""

    def __init__(self) -> None:
        super().__init__("middleware_bridge")
        self.frontend_json_sub = self.create_subscription(String, "/frontend/instructions", self._on_json, 10)
        self.typed_instruction_sub = self.create_subscription(
            FrontendInstruction, "/middleware/frontend_instruction", self._on_instruction, 10
        )
        self.action_pub = self.create_publisher(ActionRequest, "/robot/action/request", 10)
        self.lcd_pub = self.create_publisher(String, "/lcd/status", 10)
        self.speaker_pub = self.create_publisher(String, "/speaker/say", 10)
        self.frontend_done_pub = self.create_publisher(String, "/frontend/action_done", 10)
        self.done_sub = self.create_subscription(ActionDone, "/robot/action/done", self._on_done, 10)
        self.pending: Dict[str, str] = {}

    def _on_json(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self._publish_frontend_error("unknown", "unknown", f"invalid json: {exc}")
            return
        instruction = FrontendInstruction()
        instruction.header.stamp = self.get_clock().now().to_msg()
        instruction.instruction_id = str(payload.get("instruction_id", payload.get("id", "")))
        instruction.actor_id = str(payload.get("actor_id", payload.get("actor", "frontend")))
        instruction.action = str(payload.get("action", "")).lower().replace(" ", "_")
        instruction.tool = str(payload.get("tool", ""))
        instruction.target = str(payload.get("target", ""))
        instruction.json_payload = json.dumps(payload)
        loc = payload.get("estimated_location", payload.get("location", {})) or {}
        instruction.estimated_location = Point(x=float(loc.get("x", 0.0)), y=float(loc.get("y", 0.0)), z=float(loc.get("z", 0.0)))
        self._on_instruction(instruction)

    def _on_instruction(self, instruction: FrontendInstruction) -> None:
        if instruction.action not in SUPPORTED_ACTIONS:
            self._publish_frontend_error(instruction.instruction_id, instruction.actor_id, f"unsupported action {instruction.action}")
            return
        request = ActionRequest()
        request.header = instruction.header
        request.instruction_id = instruction.instruction_id
        request.actor_id = instruction.actor_id
        request.action = instruction.action
        request.tool = instruction.tool
        request.target = instruction.target
        request.target_position = instruction.estimated_location
        request.json_payload = instruction.json_payload
        request.grid_id = self._grid_from_payload(instruction.json_payload)
        self.pending[request.instruction_id] = request.actor_id
        self._status(f"{request.action}: planning")
        self.action_pub.publish(request)

    def _on_done(self, done: ActionDone) -> None:
        actor_id = self.pending.pop(done.instruction_id, done.actor_id)
        status = "done" if done.success else "failed"
        self._status(f"{done.action}: {status}")
        self.frontend_done_pub.publish(String(data=json.dumps({
            "instruction_id": done.instruction_id,
            "actor_id": actor_id,
            "subsystem": done.subsystem,
            "action": done.action,
            "success": done.success,
            "message": done.message,
        })))

    def _grid_from_payload(self, raw: str) -> str:
        try:
            return str(json.loads(raw).get("grid_id", ""))
        except json.JSONDecodeError:
            return ""

    def _status(self, text: str) -> None:
        self.lcd_pub.publish(String(data=text[:16]))
        self.speaker_pub.publish(String(data=text))

    def _publish_frontend_error(self, instruction_id: str, actor_id: str, message: str) -> None:
        self.frontend_done_pub.publish(String(data=json.dumps({
            "instruction_id": instruction_id, "actor_id": actor_id, "success": False, "message": message
        })))


def main() -> None:
    rclpy.init()
    rclpy.spin(MiddlewareBridge())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
