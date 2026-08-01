# Full End-to-End Example: Next.js Actor Picks a Pencil, Draws, and Drops Back

This walkthrough shows how one frontend command travels through the whole ROS graph and how the camera grid, ToF calibration, LCD, speaker, MoveIt executor, and completion response work together.

## 1. System startup

Launch all ROS-side processes:

```bash
ros2 launch nexus_robot_system nexus_system.launch.py
```

The launch file starts these nodes:

- `middleware_bridge`: receives Next.js JSON, creates robot action requests, and sends completion JSON back to the frontend actor.
- `moveit_action_executor`: owns the action routines and turns high-level actions into ordered motion steps.
- `yolo_grid_perception`: keeps publishing the numbered camera grid and YOLO detections.
- `tof_calibration_node`: publishes sensor offset information from the Time-of-Flight sensor.
- `lcd_status_node`: displays one-line 1x16 status messages.
- `speaker_node`: announces status phrases.

## 2. Camera grid behavior before any command

The camera node continuously publishes `/perception/grid_detections` even while no action is running. With the default config, a 640x480 image is divided into a 6x6 grid:

```text
R1C1 R1C2 R1C3 R1C4 R1C5 R1C6
R2C1 R2C2 R2C3 R2C4 R2C5 R2C6
R3C1 R3C2 R3C3 R3C4 R3C5 R3C6
R4C1 R4C2 R4C3 R4C4 R4C5 R4C6
R5C1 R5C2 R5C3 R5C4 R5C5 R5C6
R6C1 R6C2 R6C3 R6C4 R6C5 R6C6
```

For every YOLO detection, the node publishes:

- `grid_id`: the snapped cell, for example `R2C4`.
- `label`: YOLO class, for example `pencil` or `paper`.
- `confidence`: YOLO confidence.
- `center_px`: detection center in image pixels.
- `center_robot`: simple robot-frame projection using `meters_per_pixel`.
- `distance_m`: distance from the camera-center vertical virtual line.
- `snapped_to_tool`: true when the current context is `tool` or the detected class is a known tool.

The virtual line is the vertical line through the middle of the camera image. If a pencil center is at `x = 410 px`, image width is `640 px`, and `meters_per_pixel = 0.001`, the distance from the virtual line is:

```text
abs(410 - 320) * 0.001 = 0.09 m
```

The ToF sensor then helps calibrate the real camera-to-surface distance and offset.

## 3. Example frontend JSON command

A Next.js actor can publish this JSON to `/frontend/instructions` using rosbridge, a websocket gateway, or any app-specific bridge:

```json
{
  "instruction_id": "pick-draw-001",
  "actor_id": "drawing_actor_panel",
  "action": "pick_and_draw",
  "tool": "pencil",
  "target": "paper",
  "estimated_location": {"x": 0.21, "y": 0.12, "z": 0.0},
  "grid_id": "R2C4",
  "draw_path": [
    {"grid_id": "R3C2", "x": 0.10, "y": 0.20},
    {"grid_id": "R3C3", "x": 0.16, "y": 0.20},
    {"grid_id": "R4C4", "x": 0.22, "y": 0.28}
  ]
}
```

Meaning:

- `instruction_id` uniquely tracks the command until completion.
- `actor_id` tells the middleware which frontend actor should receive the final result.
- `action` selects the routine. Supported actions are `draw`, `pick`, `place`, `arc`, `pick_and_place`, `pick_and_draw`, and `drop_back`.
- `tool` tells perception and motion which object to snap to first.
- `target` tells the robot where the tool will be used.
- `estimated_location` is the frontend actor's initial estimate.
- `grid_id` is optional. If it is present, the executor can use it immediately. If it is missing, the executor picks the best matching YOLO grid detection.
- `draw_path` is preserved inside `json_payload` for the MoveIt executor or a future path planner to consume.

## 4. Middleware receives the command

The middleware converts the JSON into an `ActionRequest` and publishes it to `/robot/action/request`:

```text
instruction_id: pick-draw-001
actor_id: drawing_actor_panel
action: pick_and_draw
tool: pencil
target: paper
grid_id: R2C4
target_position:
  x: 0.21
  y: 0.12
  z: 0.0
json_payload: original JSON string
```

At the same time it publishes:

```text
/lcd/status  -> "pick_and_draw: " truncated to 16 characters when needed
/speaker/say -> "pick_and_draw: planning"
```

So the LCD might show:

```text
pick_and_draw: p
```

## 5. MoveIt executor selects the routine

For `pick_and_draw`, the executor runs this ordered routine:

```text
1. snap_tool_grid
2. grip
3. snap_paper_grid
4. trace_path
5. release
```

During each step, it also publishes a short LCD message and a perception context.

### Step 1: `snap_tool_grid`

The executor publishes:

```text
/perception/context -> "tool"
/lcd/status         -> "pick_and_draw:s" truncated to 16 characters
```

The YOLO grid node now treats detections as tool-focused. If it sees a pencil, it marks it as snapped to a tool grid cell. For example:

```text
label: pencil
grid_id: R2C4
center_px: x=410, y=130
center_robot: x=0.410, y=0.130, z=0.0
distance_m: 0.09
snapped_to_tool: true
```

The executor publishes a six-axis planning shim:

```text
/motion/stepper_command -> "plan=snap_tool_grid;grid=R2C4;axes=6"
```

In the hardware version, this is where the shim should be replaced with a MoveItPy or MoveGroupInterface plan for all six stepper axes.

### Step 2: `grip`

The executor keeps the selected tool location and closes the gripper:

```text
/lcd/status -> "pick_and_draw:g"
/motion/stepper_command -> "plan=grip;grid=R2C4;axes=6"
```

### Step 3: `snap_paper_grid`

The executor switches perception from tool snapping to paper snapping:

```text
/perception/context -> "paper"
/lcd/status         -> "pick_and_draw:s"
```

Now the single camera should identify the paper grid and publish numbered paper cells. The robot can select the path cells from the original `draw_path` or from live `/perception/grid_detections`.

### Step 4: `trace_path`

The executor traces the drawing path while the LCD shows drawing status:

```text
/lcd/status -> "pick_and_draw:t"
/motion/stepper_command -> "plan=trace_path;grid=R2C4;axes=6"
```

A production path planner should parse `draw_path` from `json_payload`, convert each grid point to robot coordinates, and send a Cartesian MoveIt trajectory.

### Step 5: `release`

The executor releases the tool or finishes the active tool operation:

```text
/lcd/status -> "pick_and_draw:r"
/motion/stepper_command -> "plan=release;grid=R2C4;axes=6"
```

## 6. Completion response returns to the same frontend actor

When the routine finishes, the executor publishes `/robot/action/done`:

```text
instruction_id: pick-draw-001
actor_id: drawing_actor_panel
subsystem: moveit_action_executor
action: pick_and_draw
success: true
message: pick_and_draw complete
```

The middleware receives that message, looks up the pending `instruction_id`, and publishes JSON to `/frontend/action_done`:

```json
{
  "instruction_id": "pick-draw-001",
  "actor_id": "drawing_actor_panel",
  "subsystem": "moveit_action_executor",
  "action": "pick_and_draw",
  "success": true,
  "message": "pick_and_draw complete"
}
```

The Next.js app should route that JSON to the actor whose id is `drawing_actor_panel`.

## 7. Standalone examples for each action

### Pick

Frontend sends:

```json
{"instruction_id":"pick-001","actor_id":"tool_actor","action":"pick","tool":"pencil","grid_id":"R2C4"}
```

Executor routine:

```text
snap_tool_grid -> approach -> grip -> retreat -> done
```

### Place

Frontend sends:

```json
{"instruction_id":"place-001","actor_id":"tool_actor","action":"place","target":"cup","grid_id":"R4C2"}
```

Executor routine:

```text
snap_target_grid -> approach -> release -> retreat -> done
```

### Draw

Frontend sends:

```json
{"instruction_id":"draw-001","actor_id":"draw_actor","action":"draw","target":"paper","grid_id":"R3C3"}
```

Executor routine:

```text
snap_paper_grid -> lower_tool -> trace_path -> raise_tool -> done
```

### Arc

Frontend sends:

```json
{"instruction_id":"arc-001","actor_id":"draw_actor","action":"arc","target":"paper","grid_id":"R3C3","radius_m":0.05,"angle_deg":90}
```

Executor routine:

```text
snap_paper_grid -> lower_tool -> trace_arc -> raise_tool -> done
```

### Pick and place

Frontend sends:

```json
{"instruction_id":"pick-place-001","actor_id":"assembly_actor","action":"pick_and_place","tool":"block","target":"tray","grid_id":"R2C2"}
```

Executor routine:

```text
snap_tool_grid -> grip -> snap_target_grid -> release -> done
```

### Pick and draw

Frontend sends:

```json
{"instruction_id":"pick-draw-002","actor_id":"drawing_actor","action":"pick_and_draw","tool":"pencil","target":"paper","grid_id":"R2C4"}
```

Executor routine:

```text
snap_tool_grid -> grip -> snap_paper_grid -> trace_path -> release -> done
```

### Drop back

Frontend sends:

```json
{"instruction_id":"drop-001","actor_id":"tool_actor","action":"drop_back","tool":"pencil"}
```

Executor routine:

```text
return_to_origin -> release -> home -> done
```

## 8. Minimal manual test commands

Publish a command:

```bash
ros2 topic pub --once /frontend/instructions std_msgs/msg/String "{data: '{\"instruction_id\":\"pick-001\",\"actor_id\":\"tool_actor\",\"action\":\"pick\",\"tool\":\"pencil\",\"grid_id\":\"R2C4\"}'}"
```

Watch the middleware request:

```bash
ros2 topic echo /robot/action/request
```

Watch LCD status:

```bash
ros2 topic echo /lcd/status
```

Watch the completion response to Next.js:

```bash
ros2 topic echo /frontend/action_done
```
