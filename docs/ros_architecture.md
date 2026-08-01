# Nexus ROS Architecture

## End-to-end flow

1. A Next.js actor publishes JSON to `/frontend/instructions` with `instruction_id`, `actor_id`, `action`, `tool`, `target`, `estimated_location`, and optional `grid_id`.
2. `middleware_bridge` validates the action, truncates a 1x16 LCD status to `/lcd/status`, optionally announces through `/speaker/say`, and publishes `/robot/action/request`.
3. `moveit_action_executor` selects the routine for `draw`, `pick`, `place`, `arc`, `pick_and_place`, `pick_and_draw`, or `drop_back`; it updates perception context so the single camera first snaps to tools for pick/draw preparation and then snaps to paper/target grids.
4. `yolo_grid_perception` continuously publishes `/perception/grid_detections`, numbering cells as `R{row}C{column}` and projecting detections into robot coordinates. A vertical virtual line through camera center is used for distance estimation, and the ToF calibration topic supplies the physical reference offset.
5. Every execution routine publishes `ActionDone` on `/robot/action/done`. The middleware converts it to JSON on `/frontend/action_done` for the original Next.js actor.

## Topic contract

| Topic | Publisher | Subscriber | Purpose |
| --- | --- | --- | --- |
| `/frontend/instructions` | Next.js bridge/rosbridge | `middleware_bridge` | Raw frontend JSON instructions. |
| `/middleware/frontend_instruction` | Optional typed frontend bridge | `middleware_bridge` | Typed equivalent of the JSON command. |
| `/robot/action/request` | `middleware_bridge` | `moveit_action_executor` | High-level action request for MoveIt planning. |
| `/perception/context` | `moveit_action_executor` | `yolo_grid_perception` | Selects `tool`, `paper`, or `target` snap mode for the single camera. |
| `/camera/image_raw` | Camera driver | `yolo_grid_perception` | Image stream for YOLO detections and grid numbering. |
| `/perception/grid_detections` | `yolo_grid_perception` | `moveit_action_executor` | Numbered grid detections with snapped tool/paper cells. |
| `/tof/range` | ToF driver | `tof_calibration_node` | Raw distance sensor data. |
| `/tof/calibration` | `tof_calibration_node` | Calibration consumers | Offset and calibration state for precise distance estimation. |
| `/motion/stepper_command` | `moveit_action_executor` | Stepper controller | Planned six-axis stepper command shim. |
| `/lcd/status` | Middleware/executor | `lcd_status_node` | 1x16 status such as `pick:planning`, `drawing`, or `done`. |
| `/speaker/say` | `middleware_bridge` | `speaker_node` | Audio output/status phrase. |
| `/robot/action/done` | Any ROS publisher/executor | `middleware_bridge` | Completion contract required after tool usage. |
| `/frontend/action_done` | `middleware_bridge` | Next.js actor | Completion JSON routed back to the actor that requested it. |

## Example pick instruction

```json
{
  "instruction_id": "pick-001",
  "actor_id": "tool_actor",
  "action": "pick",
  "tool": "pencil",
  "estimated_location": {"x": 0.21, "y": 0.12, "z": 0.0},
  "grid_id": "R2C4"
}
```

The middleware publishes `ActionRequest`, the executor sets `/perception/context` to `tool`, the YOLO grid snaps the pencil to the nearest numbered cell, MoveIt plans the six stepper axes, the LCD shows short status updates, and `/robot/action/done` returns to `/frontend/action_done` with the same `actor_id`.
