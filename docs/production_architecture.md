# Nexus Production ROS2 Workspace Architecture

This workspace now separates the robot backend into modular ROS2 packages instead of one monolithic node package. The communication rule is strict: nodes do not call each other directly; they communicate through topics, actions, and services.

## Packages

| Package | Role |
| --- | --- |
| `nexus_interfaces` | Shared strongly typed messages, action, and service definitions. |
| `middleware_bridge` | Receives Next.js JSON from rosbridge, validates it, queues requests, tracks `instruction_id`/`actor_id`, handles timeouts, publishes `ActionRequest`, and returns frontend completion JSON. |
| `execution_manager` | Robot workflow brain. It chooses a routine class, changes perception mode, calls motion planning, applies retries, and publishes `ActionDone`. |
| `perception_manager` | Owns the active perception mode state machine. |
| `yolo_grid_perception` | Continuous camera/grid publisher with stable numbered cells, virtual-line offsets, and ToF-adjusted pose output. |
| `tof_calibration` | Converts `/tof/range` into `/tof/calibration` and exposes `/tof/calibrate`. |
| `moveit_motion_controller` | C++ motion planner boundary. It receives motion plan requests and publishes `/motion/joint_trajectory`. |
| `stepper_driver` | C++ six-axis trajectory consumer that synchronously executes stepper motion. |
| `lcd_status_node` | Displays only the first 16 characters from `/lcd/status`. |
| `speaker_node` | Converts `/speaker/say` text into speech/logged output. |
| `robot_state_manager` | Observes `/robot/state` and maintains legal robot states. |
| `diagnostics_logger` | Records instruction IDs, actor IDs, state changes, durations, retry counts, and errors. |
| `camera_driver` | Reference camera publisher for `/camera/image_raw`. |

## Primary command flow

```text
Next.js Actor
  -> /frontend/instructions
middleware_bridge
  -> /robot/action/request
execution_manager
  -> /perception/context
perception_manager + yolo_grid_perception
  -> /perception/grid_detections
execution_manager
  -> /motion/plan_request
moveit_motion_controller
  -> /motion/joint_trajectory
stepper_driver
  -> /motion/stepper_status
execution_manager
  -> /robot/action/done
middleware_bridge
  -> /frontend/action_done
```

## Pick pencil example

1. Next.js publishes `{"instruction_id":"pick-001","actor_id":"tool_actor","action":"pick","tool":"pencil","grid_id":"R2C4"}`.
2. `middleware_bridge` validates required fields, queues the request, publishes `Planning` to the LCD, and emits `ActionRequest`.
3. `execution_manager` instantiates `PickRoutine`.
4. `PickRoutine` publishes `PerceptionContext(mode="SEARCH_TOOL", priority_label="pencil")`.
5. `yolo_grid_perception` keeps processing the camera, assigns the pencil to a stable grid cell, computes the virtual-line offset, adds ToF-adjusted Z, and publishes `GridDetectionArray`.
6. `execution_manager` requests motion planning.
7. `moveit_motion_controller` computes a trajectory and publishes `/motion/joint_trajectory`.
8. `stepper_driver` checks all six joint names and executes synchronously.
9. `PickRoutine` switches to `VERIFY_PICK` and then publishes `ActionDone`.
10. `middleware_bridge` returns `{"instruction_id":"pick-001","actor_id":"tool_actor","status":"DONE","success":true,"message":"pick complete"}` to `/frontend/action_done`.
