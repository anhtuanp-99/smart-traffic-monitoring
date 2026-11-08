"""Mở nguồn video và xử lý kích thước khung hình."""
import cv2

from . import config


def open_video_capture(source):
    """Mở webcam / URL stream / file video, tối ưu cho Windows."""
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)   # bật webcam nhanh trên Windows
    else:
        source = str(source)
        if not source.startswith(("http://", "https://", "rtsp://")):
            path = config.VIDEO_DIR / source
            source = str(path if path.exists() else source)
        cap = cv2.VideoCapture(source)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)                 # giảm độ trễ khi stream
    return cap


def resize_to_display(frame):
    """Thu nhỏ khung hình vừa màn hình, giữ nguyên tỉ lệ (không phóng to)."""
    h, w = frame.shape[:2]
    scale = min(config.DISPLAY_WIDTH / w, config.DISPLAY_HEIGHT / h, 1.0)
    if scale < 1.0:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    return frame