#!/usr/bin/env python3
"""MoveIt action executor coordinating six stepper axes for supported routines."""
import time
from typing import Dict, List

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from nexus_robot_system.msg import ActionDone, ActionRequest, GridDetectionArray

ROUTINES: Dict[str, List[str]] = {
    "draw": ["snap_paper_grid", "lower_tool", "trace_path", "raise_tool"],
    "pick": ["snap_tool_grid", "approach", "grip", "retreat"],
    "place": ["snap_target_grid", "approach", "release", "retreat"],
    "arc": ["snap_paper_grid", "lower_tool", "trace_arc", "raise_tool"],
    "pick_and_place": ["snap_tool_grid", "grip", "snap_target_grid", "release"],
    "pick_and_draw": ["snap_tool_grid", "grip", "snap_paper_grid", "trace_path", "release"],
    "drop_back": ["return_to_origin", "release", "home"],
}


class MoveItActionExecutor(Node):
    """Converts high-level requests into MoveIt plans and publishes completion."""

    def __init__(self) -> None:
        super().__init__("moveit_action_executor")
        self.latest_grid = GridDetectionArray()
        self.request_sub = self.create_subscription(ActionRequest, "/robot/action/request", self._on_request, 10)
        self.grid_sub = self.create_subscription(GridDetectionArray, "/perception/grid_detections", self._on_grid, 10)
        self.done_pub = self.create_publisher(ActionDone, "/robot/action/done", 10)
        self.lcd_pub = self.create_publisher(String, "/lcd/status", 10)
        self.perception_context_pub = self.create_publisher(String, "/perception/context", 10)
        self.stepper_pub = self.create_publisher(String, "/motion/stepper_command", 10)

    def _on_grid(self, msg: GridDetectionArray) -> None:
        self.latest_grid = msg

    def _on_request(self, request: ActionRequest) -> None:
        routine = ROUTINES.get(request.action)
        if not routine:
            self._done(request, False, f"unsupported routine {request.action}")
            return
        try:
            for step in routine:
                self._publish_status(f"{request.action}:{step}"[:16])
                self._set_context(step)
                self._execute_moveit_step(request, step)
            self._done(request, True, f"{request.action} complete")
        except RuntimeError as exc:
            self._done(request, False, str(exc))

    def _set_context(self, step: str) -> None:
        context = "tool" if "tool" in step else "paper" if "paper" in step else "target"
        self.perception_context_pub.publish(String(data=context))

    def _execute_moveit_step(self, request: ActionRequest, step: str) -> None:
        # Replace this shim with MoveItPy/MoveGroupInterface calls on hardware.
        grid_id = request.grid_id or self._best_grid_for(request.tool or request.target)
        self.stepper_pub.publish(String(data=f"plan={step};grid={grid_id};axes=6"))
        time.sleep(0.05)

    def _best_grid_for(self, label: str) -> str:
        label = label.lower()
        for detection in self.latest_grid.detections:
            if not label or detection.label.lower() == label:
                return detection.grid_id
        return ""

    def _publish_status(self, text: str) -> None:
        self.lcd_pub.publish(String(data=text[:16]))

    def _done(self, request: ActionRequest, success: bool, message: str) -> None:
        done = ActionDone()
        done.header.stamp = self.get_clock().now().to_msg()
        done.instruction_id = request.instruction_id
        done.actor_id = request.actor_id
        done.subsystem = "moveit_action_executor"
        done.action = request.action
        done.success = success
        done.message = message
        self.done_pub.publish(done)


def main() -> None:
    rclpy.init()
    rclpy.spin(MoveItActionExecutor())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
