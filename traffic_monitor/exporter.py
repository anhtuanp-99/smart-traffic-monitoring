"""Đánh giá ùn tắc, gợi ý đèn tín hiệu và xuất báo cáo JSON."""
import json
from datetime import datetime

from . import config


def evaluate_congestion(active_vehicles):
    if active_vehicles >= config.CONGESTION_HIGH_THRESHOLD:
        return "Cao (Un tac)"
    if active_vehicles >= config.CONGESTION_MEDIUM_THRESHOLD:
        return "Trung binh (Dong duc)"
    return "Thap (Thong thoang)"


def recommend_signal(down_total, up_total):
    ratio, min_n = config.SIGNAL_RATIO_THRESHOLD, config.SIGNAL_MIN_VEHICLES
    if down_total > up_total * ratio and down_total >= min_n:
        return "Uu tien tang thoi gian den xanh cho Lan Xuong (+15s den +20s)."
    if up_total > down_total * ratio and up_total >= min_n:
        return "Uu tien tang thoi gian den xanh cho Lan Len (+15s den +20s)."
    return "Giu nguyen chu ky den tin hieu tieu chuan cho ca 2 lan."


def _lane_info(direction_label, data):
    return {
        "direction": direction_label,
        "total_vehicles": data["total"],
        "breakdown": {name: data[name] for name in config.CLASS_NAMES.values()},
    }


def export_json_log(snapshot):
    """Ghi 1 file JSON vào logs/ từ snapshot của TrafficProcessor, trả về đường dẫn file."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()

    down = snapshot["counts"][config.DIR_DOWN]
    up = snapshot["counts"][config.DIR_UP]
    active = snapshot["active_vehicles"]

    log_data = {
        "timestamp": now.isoformat(),
        "location": config.LOCATION_NAME,
        "interval_seconds": config.EXPORT_INTERVAL_SECONDS,
        "active_vehicles_in_frame": active,
        "congestion_status": evaluate_congestion(active),
        "lane_downward": _lane_info("Bac -> Nam (Huong Xuong)", down),
        "lane_upward": _lane_info("Nam -> Bac (Huong Len)", up),
        "ai_traffic_signal_recommendation": recommend_signal(down["total"], up["total"]),
    }

    filepath = config.LOG_DIR / f"traffic_log_{now:%Y-%m-%d_%H-%M-%S}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=4)

    print(f"[LOG] Đã xuất báo cáo JSON tại: {filepath}")
    return filepath