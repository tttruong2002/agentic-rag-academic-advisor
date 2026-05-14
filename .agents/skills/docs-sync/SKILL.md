---
name: docs-sync
description: Sử dụng skill này TRƯỚC KHI commit code để tự động review các thay đổi (git diff) và đồng bộ hóa các bản cập nhật về kiến trúc, công nghệ, hoặc tiến độ vào các file tài liệu trong thư mục docs/.
---

# Docs Sync

## Mục đích
Skill này giúp dự án Khóa luận tốt nghiệp duy trì hệ thống tài liệu (`docs/`) luôn đồng bộ với mã nguồn. Thay vì phải cập nhật tài liệu lắt nhắt sau mỗi lần sửa code, skill này được thiết kế để kích hoạt ở bước cuối cùng **trước khi tạo git commit**. Bằng cách đọc `git diff`, AI sẽ hiểu toàn cục các thay đổi đã diễn ra để đưa ra quyết định cập nhật tài liệu chính xác và bao quát nhất.

## Trigger (Khi nào sử dụng)
- Khi User yêu cầu commit code (VD: "commit giúp tôi", "tạo commit").
- Khi User yêu cầu review lại code trước khi commit.
- Khi User chủ động gọi skill để đồng bộ hóa tài liệu (VD: "chạy docs-sync").

## Quy trình thực thi (Workflow)

### Bước 1: Phân tích thay đổi mã nguồn (Analyze Code Changes)
- Chạy lệnh để xem sự thay đổi của code (VD: `git diff` và `git diff --staged`).
- Đọc và hiểu ý nghĩa của các thay đổi:
  - Có thay đổi luồng logic chính nào ở Backend/Frontend không? (VD: RAG, Prompts, UI).
  - Có thêm API mới, table mới trong Database, hay hàm lõi nào mới không?
  - Có cài thêm thư viện (`requirements.txt`, `package.json`), đổi LLM model không?
  - Có cập nhật logic xử lý Data Pipeline hay Evaluation không?

### Bước 2: Xác định file docs cần cập nhật
Dựa vào phân tích ở Bước 1, đối chiếu và quyết định sẽ cập nhật vào file nào trong thư mục `docs/`:
- `ARCHITECTURE.md`: Nếu có thay đổi về luồng xử lý, thêm endpoint API, sửa DB schema.
- `ADR.md`: Nếu có các quyết định quan trọng về kiến trúc (ADR) hoặc thay đổi lớn về cách tiếp cận kỹ thuật.
- `TECH_STACK.md`: Nếu có thay đổi thư viện, model LLM/Embedding, database engine.
- `ROADMAP.md`: Nếu đoạn code vừa viết giải quyết xong 1 To-Do (thì đánh dấu `[x]`), hoặc phát sinh vấn đề mới cần ghi nhận.
- `DATA_PIPELINE.md`: Nếu sửa đổi logic parse PDF, chunking, nhúng vector DB.
- `EVALUATION.md`: Nếu cập nhật logic chấm điểm (Judge LLM) hoặc điểm số benchmark.
- `OVERVIEW.md`: Nếu cần cập nhật trạng thái high-level của dự án.

### Bước 3: Cập nhật tài liệu (Execute Updates)
- Dùng công cụ sửa file để cập nhật trực tiếp vào các file `docs/` đã xác định.
- **Quy tắc viết:** Ghi chú **cực kỳ ngắn gọn, súc tích** (dùng bullet point). Không dùng từ ngữ sáo rỗng. Bắt buộc phải chỉ rõ file code nào đã gây ra sự thay đổi này.
  - *Ví dụ TỐT:* "- Bổ sung API `/chat/history` (từ `backend/main.py`) vào luồng xử lý."
  - *Ví dụ XẤU:* "- Hệ thống đã được nâng cấp tuyệt vời bằng cách thêm lịch sử chat..."

### Bước 4: Báo cáo (Report)
- Sau khi hoàn tất cập nhật tài liệu, thông báo ngắn gọn cho User biết những gì đã được đồng bộ, và báo rằng hệ thống đã sẵn sàng để commit.
- *Ví dụ:* *"✅ Đã phân tích git diff và tự động cập nhật API mới vào `docs/ARCHITECTURE.md`, đồng thời check done mục TODO trong `docs/ROADMAP.md`. Mọi thứ đã sẵn sàng để bạn commit."*
