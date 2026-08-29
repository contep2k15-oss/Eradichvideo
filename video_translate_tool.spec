# -*- mode: python ; coding: utf-8 -*-
"""
File cấu hình PyInstaller — đóng gói desktop_app.py + toàn bộ backend/frontend
thành 1 file thực thi .exe duy nhất.

Chạy thủ công (nếu muốn build ngay trên máy, không qua GitHub Actions):
    pyinstaller video_translate_tool.spec

GitHub Actions (xem .github/workflows/build.yml) sẽ tự chạy đúng lệnh này trên
máy ảo Windows mỗi khi bạn đẩy 1 tag mới lên, không cần bạn tự build tay.
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Một số thư viện AI (đặc biệt ctranslate2 — lõi chạy của faster-whisper) có
# file nhị phân/dữ liệu đi kèm mà PyInstaller không tự dò ra hết nếu chỉ theo
# import thông thường — cần "collect_all" để gom đủ.
datas = []
binaries = []
hiddenimports = []

for pkg in ["ctranslate2", "faster_whisper", "tokenizers", "huggingface_hub"]:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Nhúng thư mục giao diện web (frontend/) vào bên trong gói — desktop_app.py
# sẽ đọc lại qua resource_path() (xem backend/config.py) để tìm đúng đường dẫn
# dù đang chạy dạng .py thường hay đã đóng gói .exe.
datas += [
    ("frontend", "frontend"),
]

hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "edge_tts",
    "anthropic",
    "google.generativeai",
]

a = Analysis(
    ["desktop_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VideoTranslateTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # Ẩn cửa sổ đen (console) — trải nghiệm app desktop thật
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico" if __import__("os").path.exists("assets/icon.ico") else None,
)
