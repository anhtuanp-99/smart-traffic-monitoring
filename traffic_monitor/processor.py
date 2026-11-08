"""Module lõi: nhận diện (YOLO) -> bám vết (ByteTrack) -> đếm xe qua vạch theo hướng."""
from collections import defaultdict, deque

import numpy as np
from ultralytics import YOLO

from . import config, drawing


class TrafficProcessor:
    PRUNE_EVERY = 300      # dọn lịch sử mỗi 300 frame
    STALE_AFTER = 150      # xe vắng mặt > 150 frame thì xóa lịch sử

    def __init__(self):
        if not config.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Không tìm thấy mô hình: {config.MODEL_PATH}\n"
                "-> Hãy đặt file best.pt vào thư mục weights/")

        print(f"[1/3] Đang nạp mô hình từ: {config.MODEL_PATH} ...")
        self.model = YOLO(str(config.MODEL_PATH))
        self.device = config.DEVICE

        print(f"[2/3] Đang khởi tạo ({self.device}) - Warm-up...")
        self.model.predict(np.zeros((640, 640, 3), dtype=np.uint8),
                           device=self.device, verbose=False)
        print("      -> Khởi tạo thành công!")

        self.track_history = defaultdict(lambda: deque(maxlen=config.TRAIL_LENGTH))
        self.last_seen = {}
        self.counted_ids = set()
        self.frame_idx = 0
        self.active_vehicles = 0
        self.counts = {
            config.DIR_DOWN: self._empty_counter(),
            config.DIR_UP: self._empty_counter(),
        }

    @staticmethod
    def _empty_counter():
        return {"total": 0, **{name: 0 for name in config.CLASS_NAMES.values()}}

    # ------------------------------------------------------------------
    def process_frame(self, frame):
        self.frame_idx += 1
        line_y = int(frame.shape[0] * config.LINE_Y_RATIO)

        results = self.model.track(
            frame, persist=True, tracker=config.TRACKER_TYPE,
            conf=config.CONFIDENCE_THRESHOLD, device=self.device, verbose=False)

        drawing.draw_count_line(frame, line_y)

        boxes = results[0].boxes
        self.active_vehicles = 0

        if boxes.id is not None:
            xywh = boxes.xywh.cpu().numpy()
            track_ids = boxes.id.int().cpu().tolist()
            class_ids = boxes.cls.int().cpu().tolist()
            self.active_vehicles = len(track_ids)

            for (cx, cy, w, h), track_id, class_id in zip(xywh, track_ids, class_ids):
                class_name = config.CLASS_NAMES.get(class_id, "unknown")
                history = self.track_history[track_id]
                history.append((int(cx), int(cy)))
                self.last_seen[track_id] = self.frame_idx

                color = drawing.draw_vehicle(frame, cx, cy, w, h, track_id, class_name)
                drawing.draw_trail(frame, history, color)
                self._count_crossing(track_id, class_name, history, line_y)

        if self.frame_idx % self.PRUNE_EVERY == 0:
            self._prune_stale_tracks()

        drawing.draw_dashboard(frame, self.counts, self.active_vehicles)
        return frame

    def _count_crossing(self, track_id, class_name, history, line_y):
        """Đếm 1 lần duy nhất khi tâm xe cắt vạch; hướng suy ra từ chiều di chuyển của trục Y."""
        if track_id in self.counted_ids or len(history) < 2:
            return

        prev_y, curr_y = history[-2][1], history[-1][1]
        if prev_y < line_y <= curr_y:
            direction = config.DIR_DOWN
        elif prev_y > line_y >= curr_y:
            direction = config.DIR_UP
        else:
            return

        bucket = self.counts[direction]
        bucket["total"] += 1
        if class_name in bucket:
            bucket[class_name] += 1
        self.counted_ids.add(track_id)

    def _prune_stale_tracks(self):
        """Xóa lịch sử của các ID đã biến mất để tránh tốn RAM khi chạy lâu."""
        stale = [tid for tid, f in self.last_seen.items()
                 if self.frame_idx - f > self.STALE_AFTER]
        for tid in stale:
            self.track_history.pop(tid, None)
            self.last_seen.pop(tid, None)

    def snapshot(self):
        """Trả về bản sao số liệu hiện tại để xuất báo cáo."""
        return {
            "counts": {d: dict(c) for d, c in self.counts.items()},
            "active_vehicles": self.active_vehicles,
        }