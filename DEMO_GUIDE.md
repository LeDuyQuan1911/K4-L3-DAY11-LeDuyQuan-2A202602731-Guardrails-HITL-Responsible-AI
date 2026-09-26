# VinBank Guardrails & Responsible AI - Demo Guide

Hệ thống Dashboard trực quan để demo toàn bộ kết quả của **Lab 11: Guardrails, HITL & Responsible AI cho Ngân hàng VinBank**.

---

## 1. Cách khởi động Demo UI

Chạy lệnh sau từ thư mục dự án:

```powershell
python run_demo.py
```
> Trình duyệt web mặc định sẽ tự động mở trang: **`http://127.0.0.1:8000`**

Nếu server đang chạy nền, bạn có thể truy cập trực tiếp vào `http://127.0.0.1:8000`.

---

## 2. Cấu trúc các Tab và Kịch bản Demo

### Tab 1: Overview & Grade Report (Tổng quan & Báo cáo chấm điểm)
* **Ý nghĩa:** Cho giảng viên/người chấm thấy trạng thái pass toàn diện của bài nộp.
* **Các chỉ số chính:**
  * **Technical Failure:** `False` (Hợp lệ 100%)
  * **Packaging:** `OK` (Đầy đủ tất cả artifact `results.json`, `attack_results.json`, `audit_log.json`, `metrics.json`)
  * **Smoke Tests:** `6/6 Passed`
  * **Public Tests:** `10/10 Passed`
  * **Red Team Attack:** 3/5 secrets rò rỉ trên Unsafe Agent (đủ điều kiện tính điểm Bonus B1), 0 rò rỉ trên Guarded Agent (100% phòng thủ thành công).
* **Nút bấm:** *View Raw Grade Report JSON* mở trực tiếp nội dung chi tiết chấm điểm.

---

### Tab 2: CP2: Guardrails (Lớp phòng thủ Input & Output)
* **Ý nghĩa:** Trình bày nguyên lý hoạt động của 2 tầng phòng thủ cốt lõi:
  1. **Input Guardrail Plugin:**
     * `detect_injection()`: Bắt các mẫu prompt injection (jailbreak, system override, bypass, sql injection, base64 payload).
     * `topic_filter()`: Từ chối các câu hỏi nằm ngoài nghiệp vụ ngân hàng (VinBank banking domain filter).
  2. **Output Guardrail Plugin:**
     * `content_filter()`: Tự động phát hiện và bôi đen/ẩn (`[REDACTED]`) các thông tin nhạy cảm: Số điện thoại Việt Nam, Email, API Keys (OpenAI, Gemini), và Secret Tokens.

---

### Tab 3: CP3: Pipeline (Quy trình thực thi & Quan sát)
* **Ý nghĩa:** Trực quan hóa dữ liệu từ `outputs/results.json`, `outputs/audit_log.json` và `outputs/metrics.json`.
* **Nội dung:**
  * Bảng thực thi 18 query chuẩn của bài lab (Safe queries, Direct attacks, Edge cases, Rate limit bursts).
  * Hiển thị trạng thái phân loại `ALLOWED` (xanh) hoặc `BLOCKED` (đỏ), kèm lý do và cảnh báo bảo mật (`ALERT`).
  * Trình xem cấu trúc `Audit Log` và thống kê `Metrics`.

---

### Tab 4: CP4: Red Team (So sánh Tấn công Red vs Red Advance)
* **Ý nghĩa:** Chứng minh năng lực của hệ thống phòng thủ Guardrails trước các cuộc tấn công jailbreak tinh vi.
* **So sánh trực diện 5 Vector tấn công:**
  1. **Base64 Payload Injection**
  2. **Developer Mode & System Instructions Override**
  3. **Fictional Scenario / IT Auditor Bypass**
  4. **Typoglycemia Obfuscation (xáo trộn ký tự từ ngữ)**
  5. **Multi-turn Context Reset**
* **Kết quả:**
  * **Unsafe Agent (Không guardrails):** Bị khai thác rò rỉ 3 bí mật `ADMIN_FLAG`, `SECRET_KEY`, `ACCOUNT_BYPASS`.
  * **Guarded Agent (Có guardrails):** 0 bí mật bị rò rỉ, 100% các cuộc tấn công bị vô hiệu hóa an toàn.

---

### Tab 5: Interactive Sandbox (Thử nghiệm Tương tác Trực tiếp)
* **Ý nghĩa:** Cho phép thầy cô hoặc người tham gia tự gõ câu hỏi hoặc thử tấn công trực tiếp.
* **Tính năng tương tác:**
  * **Quick Attack Presets:** Nút chọn nhanh 4 kịch bản (Jailbreak System Override, Topic Out-of-domain, Data Exfiltration, Valid Banking Query).
  * **Pipeline Step Execution Tracker:** Hiển thị trạng thái từng bước:
    `Rate Limit` ➔ `Injection Filter` ➔ `Topic Filter` ➔ `LLM Generation` ➔ `Output PII Redaction` ➔ `Egress Validation` ➔ `Audit Log`.
  * **Test Rate Limit Burst:** Nút mô phỏng gửi liên tiếp 8 request để chứng minh thuật toán Sliding Window chặn từ request thứ 6 với lỗi `429 Too Many Requests`.

---

## 3. Cấu trúc Source Code UI

* `web_demo/app.py`: Backend FastAPI với đầy đủ REST APIs.
* `web_demo/static/index.html`: Giao diện Dashboard Dark Mode chuẩn Fintech/Cybersecurity.
* `web_demo/static/styles.css`: Hệ thống thiết kế Glassmorphism, Neon glow, responsive modern typography.
* `web_demo/static/app.js`: Logic xử lý frontend không phụ thuộc thư viện ngoài (Vanilla JS).
* `run_demo.py`: Script khởi động 1-click tích hợp auto-browser.
