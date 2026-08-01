#!/usr/bin/env python3
"""YOLO-backed grid perception node for one-camera tool and paper localization."""
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from nexus_robot_system.msg import GridDetection, GridDetectionArray

YOLO = None  # Install ultralytics and wire image conversion before enabling model inference.


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    center_x: float
    center_y: float


class YoloGridPerception(Node):
    """Maintains a numbered paper/tool grid and snaps detections to the nearest cell."""

    def __init__(self) -> None:
        super().__init__("yolo_grid_perception")
        self.declare_parameter("rows", 6)
        self.declare_parameter("columns", 6)
        self.declare_parameter("model_path", "yolov8n.pt")
        self.declare_parameter("image_width", 640.0)
        self.declare_parameter("image_height", 480.0)
        self.declare_parameter("meters_per_pixel", 0.001)
        self.rows = int(self.get_parameter("rows").value)
        self.columns = int(self.get_parameter("columns").value)
        self.image_width = float(self.get_parameter("image_width").value)
        self.image_height = float(self.get_parameter("image_height").value)
        self.meters_per_pixel = float(self.get_parameter("meters_per_pixel").value)
        self.active_context = "paper"
        self.model = YOLO(str(self.get_parameter("model_path").value)) if YOLO else None
        self.image_sub = self.create_subscription(Image, "/camera/image_raw", self._on_image, 10)
        self.context_sub = self.create_subscription(String, "/perception/context", self._on_context, 10)
        self.grid_pub = self.create_publisher(GridDetectionArray, "/perception/grid_detections", 10)
        self.timer = self.create_timer(0.2, self._publish_empty_grid)

    def _on_context(self, msg: String) -> None:
        self.active_context = msg.data or "paper"

    def _on_image(self, image: Image) -> None:
        detections = self._run_yolo(image)
        self._publish_grid(detections, image.header)

    def _run_yolo(self, image: Image) -> List[Detection]:
        if self.model is None:
            return []
        results = self.model(image.data, verbose=False)
        detections: List[Detection] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                cls = int(box.cls[0])
                detections.append(Detection(names.get(cls, str(cls)), float(box.conf[0]), (x1 + x2) / 2.0, (y1 + y2) / 2.0))
        return detections

    def _publish_empty_grid(self) -> None:
        self._publish_grid([], None)

    def _publish_grid(self, detections: Iterable[Detection], header: Optional[object]) -> None:
        msg = GridDetectionArray()
        if header:
            msg.header = header
        else:
            msg.header.stamp = self.get_clock().now().to_msg()
        msg.rows = self.rows
        msg.columns = self.columns
        msg.cell_width_px = self.image_width / self.columns
        msg.cell_height_px = self.image_height / self.rows
        msg.active_context = self.active_context
        msg.detections = [self._to_grid_detection(d, msg.cell_width_px, msg.cell_height_px) for d in detections]
        self.grid_pub.publish(msg)

    def _to_grid_detection(self, detection: Detection, cell_w: float, cell_h: float) -> GridDetection:
        row, column = self._cell_for(detection.center_x, detection.center_y, cell_w, cell_h)
        grid = GridDetection()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.row = row
        grid.column = column
        grid.grid_id = f"R{row + 1}C{column + 1}"
        grid.label = detection.label
        grid.confidence = detection.confidence
        grid.center_px = Point(x=detection.center_x, y=detection.center_y, z=0.0)
        grid.center_robot = Point(x=detection.center_x * self.meters_per_pixel, y=detection.center_y * self.meters_per_pixel, z=0.0)
        grid.distance_m = self._virtual_line_distance(detection.center_x, detection.center_y)
        grid.snapped_to_tool = self.active_context == "tool" or detection.label.lower() in {"pencil", "pen", "marker", "eraser"}
        return grid

    def _cell_for(self, x: float, y: float, cell_w: float, cell_h: float) -> Tuple[int, int]:
        column = min(max(int(x // cell_w), 0), self.columns - 1)
        row = min(max(int(y // cell_h), 0), self.rows - 1)
        return row, column

    def _virtual_line_distance(self, x: float, y: float) -> float:
        # Distance from the camera-center vertical virtual line; calibrate meters_per_pixel with ToF.
        return abs(x - (self.image_width / 2.0)) * self.meters_per_pixel


def main() -> None:
    rclpy.init()
    rclpy.spin(YoloGridPerception())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
