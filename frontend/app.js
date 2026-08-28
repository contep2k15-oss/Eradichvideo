const API = "/api";

// Nhãn hiển thị cho từng trạng thái, đúng thứ tự 12 bước đã thiết kế
const STEP_LABELS = [
  { key: "extracting", label: "Bước 1-2 · Tải video & tách audio" },
  { key: "detecting_culture", label: "Bước 3 · Phát hiện điểm nhạy văn hóa" },
  { key: "translating", label: "Bước 4 · Dịch sát nghĩa" },
  { key: "localizing_humor", label: "Bước 5 · Bản địa hóa hài / chơi chữ" },
  { key: "qa_checking", label: "Bước 6 · Kiểm tra ngược (QA)" },
  { key: "awaiting_review", label: "Bước 7 · Chờ bạn duyệt lại" },
  { key: "synthesizing_voice", label: "Bước 8 · Tạo giọng lồng tiếng" },
  { key: "syncing_timing", label: "Bước 9 · Đồng bộ thời lượng" },
  { key: "building_subtitles", label: "Bước 10 · Sinh phụ đề" },
  { key: "muxing", label: "Bước 11 · Ghép audio + video" },
  { key: "exporting", label: "Bước 12 · Xuất theo định dạng nền tảng" },
  { key: "done", label: "Hoàn tất" },
];

let currentJobId = null;
let pollTimer = null;

// ---------- Tabs ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "jobs") loadJobsList();
  });
});

// ---------- Nguồn: link vs file ----------
document.querySelectorAll(".src-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".src-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const isUrl = btn.dataset.src === "url";
    document.getElementById("field-url").classList.toggle("hidden", !isUrl);
    document.getElementById("field-file").classList.toggle("hidden", isUrl);
  });
});

// ---------- Submit job mới ----------
document.getElementById("job-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append("target_lang", document.getElementById("target_lang").value);

  const sourceLang = document.getElementById("source_lang").value.trim();
  if (sourceLang) formData.append("source_lang", sourceLang);

  const genre = document.getElementById("content_genre").value;
  if (genre) formData.append("content_genre", genre);

  const urlActive = document.querySelector('.src-btn[data-src="url"]').classList.contains("active");
  if (urlActive) {
    const url = document.getElementById("source_url").value.trim();
    if (!url) return alert("Vui lòng dán link video");
    formData.append("source_url", url);
  } else {
    const file = document.getElementById("source_file").files[0];
    if (!file) return alert("Vui lòng chọn file video");
    formData.append("file", file);
  }

  const res = await fetch(`${API}/jobs`, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert("Lỗi tạo job: " + (err.detail || res.statusText));
  }
  const data = await res.json();
  currentJobId = data.job_id;

  document.getElementById("progress-card").classList.remove("hidden");
  document.getElementById("review-card").classList.add("hidden");
  document.getElementById("result-card").classList.add("hidden");
  document.getElementById("current-job-id").textContent = currentJobId;

  renderSteps("extracting");
  startPolling();
});

// ---------- Render thanh tiến trình ----------
function renderSteps(activeKey, failed = false) {
  const track = document.getElementById("steps-track");
  track.innerHTML = "";
  let reachedActive = false;

  STEP_LABELS.forEach((step) => {
    const li = document.createElement("li");
    const dot = document.createElement("span");
    dot.className = "dot";
    li.appendChild(dot);
    li.appendChild(document.createTextNode(step.label));

    if (step.key === activeKey) {
      li.className = failed ? "failed" : "active";
      reachedActive = true;
    } else if (!reachedActive) {
      li.className = "done";
    }
    track.appendChild(li);
  });
}

// ---------- Polling trạng thái job ----------
function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollJobStatus, 2500);
  pollJobStatus();
}

async function pollJobStatus() {
  if (!currentJobId) return;
  const res = await fetch(`${API}/jobs/${currentJobId}`);
  if (!res.ok) return;
  const job = await res.json();

  renderSteps(job.status, job.status === "failed");

  if (job.status === "failed") {
    clearInterval(pollTimer);
    alert("Job lỗi: " + (job.error || "không rõ nguyên nhân"));
    return;
  }

  if (job.status === "awaiting_review") {
    clearInterval(pollTimer);
    await loadReviewTable();
  }

  if (job.status === "done") {
    clearInterval(pollTimer);
    renderResults(job);
  }
}

// ---------- Bước 7: bảng review ----------
async function loadReviewTable() {
  const res = await fetch(`${API}/jobs/${currentJobId}/review`);
  if (!res.ok) return;
  const segments = await res.json();

  const tbody = document.getElementById("review-tbody");
  tbody.innerHTML = "";

  segments.forEach((s) => {
    const tr = document.createElement("tr");
    if (s.qa_flag) tr.classList.add("flag-qa");
    else if (s.is_culture_sensitive) tr.classList.add("flag-culture");

    const finalText = s.human_edited_text || s.localized_translation || s.literal_translation || "";

    let noteHtml = "";
    if (s.qa_flag) noteHtml += `<span class="tag tag-qa">QA cảnh báo</span><br/>${s.qa_note || ""}`;
    else if (s.is_culture_sensitive) noteHtml += `<span class="tag tag-culture">Đã bản địa hóa</span><br/>${s.culture_note || ""}`;

    tr.innerHTML = `
      <td>${s.id}</td>
      <td>${escapeHtml(s.source_text)}</td>
      <td class="note-cell">${noteHtml}</td>
      <td><textarea data-id="${s.id}">${escapeHtml(finalText)}</textarea></td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("review-card").classList.remove("hidden");
}

document.getElementById("submit-review-btn").addEventListener("click", async () => {
  const textareas = document.querySelectorAll("#review-tbody textarea");
  const edits = Array.from(textareas).map((ta) => ({
    id: parseInt(ta.dataset.id, 10),
    edited_text: ta.value,
  }));

  const btn = document.getElementById("submit-review-btn");
  btn.disabled = true;
  btn.textContent = "Đang xử lý...";

  const res = await fetch(`${API}/jobs/${currentJobId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edits }),
  });

  if (!res.ok) {
    alert("Lỗi khi gửi review");
    btn.disabled = false;
    btn.textContent = "Duyệt xong → Lồng tiếng & xuất video (bước 8 → 12)";
    return;
  }

  document.getElementById("review-card").classList.add("hidden");
  renderSteps("synthesizing_voice");
  startPolling();
});

// ---------- Kết quả ----------
function renderResults(job) {
  const box = document.getElementById("result-links");
  box.innerHTML = "";

  addResultLink(box, "Video hoàn chỉnh (gốc, chưa crop nền tảng)", `${API}/jobs/${currentJobId}/download/final`);
  addResultLink(box, "File phụ đề (.srt)", `${API}/jobs/${currentJobId}/download/subtitle`);

  Object.keys(job.export_paths || {}).forEach((platform) => {
    addResultLink(box, `Bản xuất: ${platform}`, `${API}/jobs/${currentJobId}/download/${platform}`);
  });

  document.getElementById("result-card").classList.remove("hidden");
}

function addResultLink(container, label, href) {
  const row = document.createElement("div");
  row.className = "result-link";
  row.innerHTML = `<span class="label">${label}</span><a href="${href}" target="_blank">Tải xuống ↓</a>`;
  container.appendChild(row);
}

// ---------- Danh sách job ----------
async function loadJobsList() {
  const res = await fetch(`${API}/jobs`);
  if (!res.ok) return;
  const jobs = await res.json();
  const box = document.getElementById("jobs-list");
  box.innerHTML = "";

  if (jobs.length === 0) {
    box.innerHTML = `<p class="hint">Chưa có job nào.</p>`;
    return;
  }

  jobs.forEach((job) => {
    const row = document.createElement("div");
    row.className = "job-row";
    row.innerHTML = `
      <span>${job.id} — ${job.target_lang}</span>
      <span class="status-pill">${job.status}</span>
    `;
    row.style.cursor = "pointer";
    row.addEventListener("click", () => {
      currentJobId = job.id;
      document.querySelector('.tab-btn[data-tab="new"]').click();
      document.getElementById("progress-card").classList.remove("hidden");
      document.getElementById("current-job-id").textContent = currentJobId;
      startPolling();
    });
    box.appendChild(row);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}
