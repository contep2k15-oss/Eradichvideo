"""
Điểm khởi chạy dạng app desktop — thay thế cho việc gõ `uvicorn backend.main:app`
rồi tự mở trình duyệt.

Chạy server FastAPI ở 1 luồng nền (background thread), rồi mở 1 CỬA SỔ APP RIÊNG
bằng pywebview trỏ vào server đó — giống hệt trải nghiệm 1 app desktop thật
(không thấy thanh địa chỉ trình duyệt, không có tab khác), tương đương với việc
Electron mở cửa sổ Chromium riêng cho app của nó ở repo mẫu.

File này là entry point khi build bằng PyInstaller (xem video_translate_tool.spec).
Khi phát triển bình thường (chưa đóng gói), vẫn có thể chạy trực tiếp:
    python desktop_app.py
"""
import threading
import time
import sys
import os

# Đảm bảo import được package "backend" dù chạy từ đâu (kể cả khi đã đóng gói .exe)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HOST = "127.0.0.1"
PORT = 8000


def _run_server():
    import uvicorn
    from backend.main import app

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def _wait_for_server_ready(timeout: float = 20.0) -> bool:
    """Chờ server FastAPI sẵn sàng nhận request trước khi mở cửa sổ, tránh
    hiện màn hình trắng/lỗi kết nối trong vài giây đầu lúc server đang khởi động."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/api/jobs", timeout=1)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.3)
    return False


def main():
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    if not _wait_for_server_ready():
        print("LỖI: Server không khởi động được sau 20 giây. Kiểm tra file .env "
              "và log để biết chi tiết.")
        input("Nhấn Enter để thoát...")
        sys.exit(1)

    import webview

    webview.create_window(
        title="Video Translate Tool",
        url=f"http://{HOST}:{PORT}",
        width=1180,
        height=800,
        min_size=(900, 640),
    )
    webview.start()


if __name__ == "__main__":
    main()
