"""Cấu hình tập trung cho toàn bộ hệ thống. Chỉ cần sửa file này khi đổi tham số."""
from pathlib import Path

try:
    import torch
    DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"

# ==============================================================================
# 1. ĐƯỜNG DẪN
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent      # thư mục gốc dự án (train_model/)
MODEL_PATH = BASE_DIR / "weights" / "best.pt"
VIDEO_DIR = BASE_DIR / "video"
LOG_DIR = BASE_DIR / "logs"

# ==============================================================================
# 2. NGUỒN VIDEO
# ==============================================================================
#   0                                  -> Webcam laptop
#   "http://192.168.1.X:8080/video"    -> Camera điện thoại (IP Webcam / DroidCam)
#   "traffic_video_1.mp4"              -> File trong thư mục video/

# VIDEO_SOURCE = 0
VIDEO_SOURCE = "http://192.168.2.4:8080/video"

# Kích thước tối đa của cửa sổ hiển thị (giữ nguyên tỉ lệ khung hình)
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
WINDOW_NAME = "He Thong Giam Sat Giao Thong (Nhan Q, ESC hoac X de thoat)"

# ==============================================================================
# 3. MÔ HÌNH & TRACKING
# ==============================================================================
CLASS_NAMES = {0: "car", 1: "motorbike", 2: "bus", 3: "truck"}

# Màu BGR cho từng loại xe
CLASS_COLORS = {
    "car": (0, 255, 0),
    "motorbike": (0, 165, 255),
    "bus": (255, 0, 255),
    "truck": (0, 0, 255),
}

TRACKER_TYPE = "bytetrack.yaml"
CONFIDENCE_THRESHOLD = 0.35     # ngưỡng tự tin tối thiểu (35%)

# ==============================================================================
# 4. ĐẾM XE & PHÂN LÀN
# ==============================================================================
LINE_Y_RATIO = 0.55             # vạch đếm nằm ở 55% chiều cao khung hình (từ trên xuống)
TRAIL_LENGTH = 30               # số điểm quỹ đạo lưu cho mỗi xe

DIR_DOWN = "direction_down"     # trên -> dưới (Bắc -> Nam)
DIR_UP = "direction_up"         # dưới -> trên (Nam -> Bắc)

# ==============================================================================
# 5. ĐÁNH GIÁ ÙN TẮC (số xe xuất hiện cùng lúc trong khung hình)
# ==============================================================================
CONGESTION_MEDIUM_THRESHOLD = 8     # >= 8 xe: Đông đúc
CONGESTION_HIGH_THRESHOLD = 15      # >= 15 xe: Ùn tắc

# Gợi ý đèn tín hiệu: lưu lượng 1 chiều phải gấp bao nhiêu lần chiều kia và tối thiểu bao nhiêu xe
SIGNAL_RATIO_THRESHOLD = 1.5
SIGNAL_MIN_VEHICLES = 5

# ==============================================================================
# 6. XUẤT JSON
# ==============================================================================
EXPORT_INTERVAL_SECONDS = 60
LOCATION_NAME = "Nut giao thong Da Nang - Camera 01"