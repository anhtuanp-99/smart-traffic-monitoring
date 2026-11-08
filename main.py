"""Điểm khởi chạy chương trình:  python main.py"""
import time

import cv2
import numpy as np

from traffic_monitor import config
from traffic_monitor.exporter import export_json_log
from traffic_monitor.processor import TrafficProcessor
from traffic_monitor.video_source import open_video_capture, resize_to_display


def show_loading_screen(window_name, message):
    """Hiện màn hình chờ ngay lập tức để người dùng biết chương trình đang chạy."""
    img = np.zeros((480, 800, 3), dtype=np.uint8)
    cv2.putText(img, message, (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.imshow(window_name, img)
    cv2.waitKey(1)


def main():
    window = config.WINDOW_NAME
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    show_loading_screen(window, "Dang khoi tao model YOLOv8...")

    processor = TrafficProcessor()

    print(f"[3/3] Đang kết nối nguồn video ({config.VIDEO_SOURCE})...")
    show_loading_screen(window, "Dang mo nguon video...")
    cap = open_video_capture(config.VIDEO_SOURCE)

    if not cap.isOpened():
        print(f"[LỖI] Không thể mở nguồn video: {config.VIDEO_SOURCE}")
        cv2.destroyAllWindows()
        return

    print("--- HỆ THỐNG ĐÃ SẴN SÀNG! --- Nhấn 'q', 'ESC' hoặc nút 'X' để thoát.")
    last_export = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[INFO] Kết thúc luồng video hoặc mất tín hiệu camera.")
                break

            frame = resize_to_display(frame)
            cv2.imshow(window, processor.process_frame(frame))

            if time.time() - last_export >= config.EXPORT_INTERVAL_SECONDS:
                export_json_log(processor.snapshot())
                last_export = time.time()

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                print("[INFO] Người dùng đã nhấn phím thoát.")
                break
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                print("[INFO] Người dùng đã đóng cửa sổ.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Đã dừng bằng Ctrl+C.")

    finally:
        print("[INFO] Đang lưu báo cáo cuối cùng vào logs/ ...")
        export_json_log(processor.snapshot())
        cap.release()
        cv2.destroyAllWindows()
        print("[HOÀN TẤT] Đã đóng chương trình an toàn.")


if __name__ == "__main__":
    main()