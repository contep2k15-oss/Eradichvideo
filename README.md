# Tool Dịch Video Đa Ngôn Ngữ

> 📦 Dự án này đã được đóng gói sẵn dạng git repo (có `.gitignore`, `LICENSE`, 1 commit khởi tạo).
> Xem mục **"Đưa lên GitHub của riêng bạn"** ở cuối file để tải về và dùng ngay.

App web đơn giản chạy local, thực hiện đầy đủ pipeline 12 bước:
tải video → tách audio → ASR (Whisper) → phát hiện điểm nhạy văn hóa →
dịch sát nghĩa → bản địa hóa hài/chơi chữ → QA dịch ngược → **review con người** →
TTS lồng tiếng → đồng bộ thời lượng → phụ đề → ghép video → xuất theo định dạng nền tảng
(không tự động đăng).

Thiết kế tối ưu cho máy có **GPU 6GB VRAM** (GTX 1660 Ti/Super) chạy local, chỉ trả phí cho
phần gọi LLM API ở bước dịch/bản địa hóa.

## 1. Cài đặt hệ thống (một lần)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip

# Kiểm tra ffmpeg có NVENC không (khuyến nghị để encode nhanh, không tốn VRAM AI)
ffmpeg -encoders 2>&1 | grep nvenc
```

Windows: cài [ffmpeg](https://ffmpeg.org/download.html) và thêm vào PATH, cài Python 3.10+.

## 2. Cài Python packages

```bash
cd video_translate_tool
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> Nếu máy có GPU NVIDIA, cài thêm `torch` bản có CUDA phù hợp driver của bạn trước khi cài
> `faster-whisper` để tận dụng GPU (xem hướng dẫn tại pytorch.org — chọn đúng bản CUDA).

## 3. Cấu hình API key

```bash
cp .env.example .env
```

Mở `.env` và điền:
- `LLM_PROVIDER=gemini` (hoặc `anthropic`)
- `GEMINI_API_KEY=...` hoặc `ANTHROPIC_API_KEY=...`

Với GPU 6GB, giữ nguyên mặc định trong `.env.example`:
- `WHISPER_MODEL_SIZE=distil-large-v3`
- `WHISPER_COMPUTE_TYPE=int8`

## 4. Chạy app

```bash
uvicorn backend.main:app --reload --port 8000
```

Mở trình duyệt tại **http://localhost:8000**

## 5. Cách dùng

1. Tab **Job mới**: dán link video (YouTube/TikTok/Facebook) hoặc upload file, chọn ngôn ngữ đích.
2. App tự chạy bước 1→6 (tải, tách audio, ASR, phát hiện văn hóa, dịch, bản địa hóa, QA).
3. Khi tới **bước 7**, màn hình review hiện ra — dòng cam là đoạn đã bản địa hóa hài,
   dòng đỏ là đoạn AI cảnh báo có thể lệch nghĩa. Sửa trực tiếp trong ô text nếu cần,
   rồi bấm **"Duyệt xong"**.
4. App tiếp tục chạy bước 8→12 (TTS, đồng bộ, phụ đề, ghép video, xuất theo nền tảng).
5. Tải video hoàn chỉnh, file phụ đề `.srt`, và các bản đã crop theo từng nền tảng —
   **tự tải lên các nền tảng theo cách thủ công**, app không tự động đăng bài.

## Ghi chú vận hành với GPU 6GB

- `faster-whisper` giữ nguyên tắc load model rồi giải phóng VRAM ngay sau khi transcribe xong
  (xem `backend/pipeline/step2_asr.py`), để nhường VRAM cho các bước sau nếu bạn có bật thêm
  model local khác.
- Mặc định TTS dùng **Edge-TTS** (cloud, free, không tốn VRAM). Nếu muốn voice cloning bằng
  XTTS-v2 chạy local, cần tự thêm module riêng và đảm bảo không chạy đồng thời với Whisper.
- Bước 11-12 dùng `h264_nvenc` (encoder riêng của GPU, tách biệt VRAM dùng cho AI); nếu máy
  không có NVENC, code tự động fallback về `libx264` (CPU).

## Cấu trúc thư mục

```
backend/
  main.py                # FastAPI app + API endpoints
  config.py               # đọc .env
  models.py                # Job, Segment (pydantic)
  job_store.py             # lưu job dạng JSON file (đơn giản, 1 người dùng)
  llm_client.py             # gọi Gemini/Anthropic, dùng chung cho bước 3-6
  pipeline_runner.py        # điều phối toàn bộ 12 bước
  pipeline/
    step1_2_input_extract.py
    step2_asr.py
    step3_culture_detect.py
    step4_translate.py
    step5_localize_humor.py
    step6_backtranslate_qa.py
    step8_tts.py
    step9_sync.py
    step10_subtitles.py
    step11_mux.py
    step12_export.py
frontend/
  index.html / style.css / app.js   # UI web đơn giản, không cần build tool
jobs/                        # dữ liệu từng job (transcript, audio, video xuất ra)
```

## Đưa lên GitHub của riêng bạn

Dự án đã có sẵn git repo cục bộ (1 commit khởi tạo), bạn chỉ cần tạo repo trống trên
GitHub rồi trỏ về đó. Không cần biết git chuyên sâu, làm theo đúng các bước sau:

### Cách 1 — Dùng dòng lệnh (nhanh nhất)

1. Vào **github.com** → bấm **New repository** → đặt tên (VD: `video-translate-tool`) →
   **không** tick "Add a README" (vì repo này đã có sẵn) → **Create repository**.
2. GitHub sẽ hiện ra 1 đường link dạng `https://github.com/<ten-ban>/video-translate-tool.git`
   — copy link đó.
3. Mở terminal tại thư mục dự án đã giải nén, chạy:

```bash
git remote add origin https://github.com/<ten-ban>/video-translate-tool.git
git branch -M main
git push -u origin main
```

4. Nhập tài khoản/Personal Access Token GitHub khi được hỏi (GitHub không còn nhận mật khẩu
   thường qua dòng lệnh — vào **Settings → Developer settings → Personal access tokens** trên
   GitHub để tạo token nếu chưa có).

Từ lần sau, mỗi khi sửa code chỉ cần:
```bash
git add -A && git commit -m "Mô tả thay đổi" && git push
```

### Cách 2 — Không cần dòng lệnh (kéo-thả qua web)

1. Tạo repo trống trên GitHub như bước 1 ở trên.
2. Vào trang repo vừa tạo → **Add file → Upload files**.
3. Kéo-thả toàn bộ các file/thư mục đã giải nén vào (trừ thư mục `jobs/` và file `.env`
   nếu có — không nên đưa API key lên GitHub).
4. Bấm **Commit changes**.

### Sau khi đã có repo trên GitHub — người khác/máy khác tải về dùng thế nào

```bash
git clone https://github.com/<ten-ban>/video-translate-tool.git
cd video-translate-tool
cp .env.example .env    # rồi điền API key vào .env
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

⚠️ **Không bao giờ commit file `.env`** (đã có sẵn trong `.gitignore`) vì file này chứa API
key riêng của bạn — nếu lỡ đưa lên GitHub public, người khác có thể lấy trộm key và dùng
tốn tiền tài khoản của bạn. Nếu lỡ commit rồi, phải thu hồi (revoke) key đó ngay trên trang
Gemini/Anthropic và tạo key mới.

## Giới hạn của bản này (đáng biết trước khi dùng thật)

- `job_store.py` lưu bằng file JSON, phù hợp 1 người dùng chạy local — nếu nhiều người dùng
  cùng lúc hoặc cần chạy production, nên đổi sang database thật (PostgreSQL/SQLite) và
  queue thật (Celery/RQ) thay vì `BackgroundTasks` của FastAPI.
- Chưa có xác thực người dùng (auth) — app này thiết kế chạy local trên máy riêng.
- `step8_tts.py` mặc định 1 giọng/ngôn ngữ; muốn nhiều giọng hoặc voice cloning cần mở rộng
  thêm (đã có gợi ý XTTS-v2 trong tài liệu thiết kế trước đó).
