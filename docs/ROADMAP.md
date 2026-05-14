# Lộ trình & To-Do

## Phase 1: Data Pipeline Nâng cấp

- [x] Trích xuất text thô: Docling + UnstructuredPDFLoader (`01_Raw_Extraction`)
- [x] Làm sạch bằng Gemini Flash API (`02_Refinement_Merge`)
- [ ] **[MỚI] Notebook `00_Gemini_PDF_Parser`**: Upload PDF trực tiếp lên Gemini Files API, batch ~10-20 trang/lần, thay thế pipeline cũ
- [ ] **[MỚI] Context Caching**: Sử dụng Gemini Context Caching khi gọi nội dung PDF trùng lặp để tiết kiệm chi phí
- [ ] Chuẩn hóa bảng biểu → JSON Minified trong prompt Gemini
- [ ] Chunking theo ngữ nghĩa: `MarkdownHeaderTextSplitter` thay vì token/char
- [ ] Nạp lại toàn bộ data vào ChromaDB sau pipeline mới

## Phase 2: Backend Hoàn thiện

- [x] Cài đặt PostgreSQL, cấu hình `.env`
- [x] SQLModel: User, Conversation, ChatTurn
- [x] Key Rotation + Generator Fallback 2 tầng
- [x] API `/chat` với Self-Correction Loop
- [x] API `/chat/history` load 10 lượt gần nhất
- [ ] Cập nhật API `/chat` nhận `conversation_id` để tự động nhét lịch sử chat vào ngữ cảnh
- [ ] Tạo module CRUD đơn giản cho các thao tác Database
- [ ] Database Migrations (Alembic) cho production
- [ ] Thêm `tenacity` cho Exponential Backoff
- [ ] Tích hợp Hybrid Search (ChromaDB Vector + BM25 Sparse) để tìm kiếm mã môn/lớp chính xác
- [ ] Semantic Cache (Redis/SQLite) cho câu hỏi trùng
- [ ] Multi-provider rotation: Groq → OpenRouter → 9Router

## Phase 3: Frontend Chuyển đổi

- [x] Streamlit chat interface + Thinking Mode
- [ ] Tạm ngưng các tính năng Auth trên Streamlit để dồn sức chuẩn hóa API Backend (`/v1/chat`, `/v1/auth`, `/v1/conversations`)
- [ ] Thống nhất JSON interface Backend trả về (để khi dựng xong ReactJS, chỉ cần "lắp ráp" thẳng vào)
- [ ] Design kiến trúc ReactJS cơ bản
- [ ] Xây dựng React chat UI thay thế Streamlit

## Phase 4: Evaluation & Báo cáo

- [x] Bộ 150 câu hỏi benchmark
- [x] Evaluation Naive RAG (Notebook 04)
- [x] Evaluation Agentic RAG (Notebook 05)
- [ ] So sánh kết quả trước/sau nâng cấp pipeline
- [ ] Hoàn thiện báo cáo KLTN

## Vấn đề đã biết

### Dữ liệu (ChromaDB)
- Chunk đôi khi thiếu tiêu đề nguồn gốc (context bị đứt gãy)
- Ký tự rác từ header/footer PDF trộn vào text
- Bảng biểu vỡ cấu trúc khi parse PDF (đặc biệt bảng scan)
- **Giải pháp đang áp dụng**: Hybrid Extraction (Docling + Unstructured + Gemini Flash)
- **Định hướng mới**: Dùng Gemini API làm PDF Parser chính

### Rate Limit (Groq)
- TPM thấp (6K-12K tùy model)
- **Đã giải quyết**: Shuffle Key Rotation (10 keys) + Robust Resume
- **Tương lai**: Multi-provider (OpenRouter, 9Router)
