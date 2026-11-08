"""Các hàm vẽ lên khung hình (vạch đếm, bounding box, quỹ đạo, dashboard)."""
import cv2
import numpy as np

from . import config


def draw_count_line(frame, line_y):
    width = frame.shape[1]
    cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2)
    cv2.putText(frame, "VACH DEM XE A/B", (20, line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


def draw_vehicle(frame, cx, cy, w, h, track_id, class_name):
    color = config.CLASS_COLORS.get(class_name, (0, 255, 0))
    x1, y1 = int(cx - w / 2), int(cy - h / 2)
    x2, y2 = int(cx + w / 2), int(cy + h / 2)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, f"ID:{track_id} {class_name}", (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return color


def draw_trail(frame, points, color):
    if len(points) >= 2:
        pts = np.array(points, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(frame, [pts], False, color, 2)


def draw_dashboard(frame, counts, active_vehicles):
    down, up = counts[config.DIR_DOWN], counts[config.DIR_UP]

    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (540, 115), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    def line(d):
        return f"{d['total']} (Bike:{d['motorbike']} | Car:{d['car']} | Bus:{d['bus']} | Truck:{d['truck']})"

    cv2.putText(frame, f"Huong Xuong: {line(down)}", (20, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
    cv2.putText(frame, f"Huong Len:   {line(up)}", (20, 72),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 180, 0), 2)
    cv2.putText(frame, f"Xe trong khung hinh: {active_vehicles} | Nhan 'q' hoac 'ESC' de thoat",
                (20, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 200), 1)