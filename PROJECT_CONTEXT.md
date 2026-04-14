# Ngữ cảnh dự án: Nâng cao hiệu quả hệ thống tư vấn học vụ bằng kiến trúc Agentic RAG kết hợp kỹ thuật tìm kiếm lai (Khóa luận tốt nghiệp ngành Kỹ thuật dữ liệu)

## Tổng quan
Dự án là một hệ thống Chatbot tư vấn học vụ dành cho sinh viên trường Đại học Công nghệ Kỹ thuật TP.HCM (HCMUTE), dựa trên quy chế đào tạo và sổ tay sinh viên.
Hệ thống hiện tại đã được nâng cấp lên cấu trúc **Agentic RAG** với khả năng định tuyến ý định (Intent Routing), viết lại truy vấn (Query Rewriting), và tự kiểm lỗi (Self-Correction).

## Kiến trúc hiện tại (Agentic RAG)
1. **Frontend**: Xây dựng bằng `Streamlit` (`frontend/app.py`). Có giao diện chat, tích hợp thanh trạng thái (`st.status`) thể hiện tiến trình suy nghĩ của AI.
   - Hỗ trợ nút **Chế độ Suy nghĩ (Thinking Mode)**, cho phép Agent retry tối đa 3 lần nếu context ban đầu chưa cung cấp đủ dữ kiện.
2. **Backend**: Xây dựng bằng `FastAPI` với cấu trúc Moduler phân tách rõ ràng (chuẩn bị cho mở rộng React):
   - `backend/main.py`: Controller chính chạy server Uvicorn và API endpoint.
   - `backend/database.py`: Quản lý Database ORM (SQLModel) liên kết PostgreSQL lưu lịch sử Chat(`User`, `Conversation`, `ChatTurn`).
   - `backend/llm_agent.py`: Service chứa logic các Chains Mô hình Groq, Prompts, Hàm lõi tự sửa lỗi `run_agentic_rag`.
   - `backend/vector_store.py`: Tách riêng phần load ChromaDB và tài nguyên Nhúng dữ liệu (Embedding Model CPU).
3. **Database**: 
   - Vector Search: `ChromaDB` cục bộ tại thư mục `chroma_db`.
   - Database SQL: `PostgreSQL` (Khai báo trong `.env` là `DATABASE_URL`) truy vấn bằng `SQLModel`. Quản lý luồng lịch sử hỏi đáp.
4. **Mô hình (LLM & Embeddings)**:
   - **Embedding**: `Alibaba-NLP/gte-multilingual-base` (chạy trên CPU cục bộ).
   - **Agent Router & Rewriter**: `llama-3.1-8b-instant` (tốc độ cao để phân luồng và chỉnh sửa câu truy vấn ngầm).
   - **Agent Generator**: `groq/compound-mini` (model lớn để tập trung đọc context dài và sinh câu trả lời tự nhiên).

## Luồng xử lý dữ liệu tiền kỳ (Data Pipeline)
Dự án bao gồm các file Jupyter Notebook để xử lý dữ liệu và đánh giá:
- `01_Raw_Extraction.ipynb`: Trích xuất dữ liệu gốc dạng thô từ PDF hoặc tài liệu thô.
- `02_Refinement_Merge.ipynb`: Tinh chỉnh dữ liệu text, chia đoạn (chunking), gom nhóm chuẩn bị vector hóa. (Kết quả có xuất ra text `merged_documents.txt`).
### Đánh giá (Evaluation)
- `150questions.txt`: Bộ 150 câu hỏi benchmark mới (thay thế 50 câu).
- `03_Evaluation_RAG.ipynb`: Thử nghiệm mô hình RAG ban đầu (cũ).
- `04_Evaluation_Single_Model.ipynb`: [Mới] Đánh giá RAG cơ bản (Naive RAG) với 1 mô hình `groq/compound-mini` trên 150 câu hỏi.
- `05_Evaluation_Agentic_RAG.ipynb`: [Mới] So sánh hiệu quả RAG tự đổi câu hỏi (Agentic) với Naive RAG, thống kê tỉ lệ Retry và cải thiện điểm số.

## Luồng Backend RAG Agentic (Hoạt động thực tế)
Hệ thống API `/chat` gồm 2 bước chính:
**1. Intent Routing (Phân luồng ý định)**
- Nhận `question` từ user, đi qua `llm_router`.
- Nếu Intent là **GREETING** (giao tiếp thông thường, hỏi thăm bản thân AI): Trả về kết quả giao tiếp ngay, bỏ qua CSDL.
- Nếu Intent là **RAG** (tìm thông tin nghiệp vụ/quy chế): Bắt đầu vòng lặp truy xuất dữ liệu.

**2. Vòng lặp Self-Correction Loop**
- Nhúng `current_query` (vòng 1 là câu hỏi gốc) và gọi `retriever` lấy top chunks tài liệu.
- Generator xử lý và ép cấu trúc output sang dạng hàm JSON: `{"is_found": true/false, "answer": "..."}`.
- Nếu `is_found == true`: Tìm thấy thông tin, thoát vòng lặp và trả về cho Client.
- Nếu `is_found == false`: Context không đủ để giải đáp.
  - Khi đó, hệ thống sẽ gọi **Rewriter Agent** sinh ra `rewritten_query` mới tinh chỉnh từ câu hỏi cũ và các từ viết tắt học vụ (dktc, kltn...).
  - Vòng lặp RAG sẽ xoay vòng với `current_query` mới (số lần lặp tối đa phụ thuộc cờ `is_thinking`).
  
*Lưu ý: Để đối mặt với việc các model mở (Llama 3.1) thỉnh thoảng sinh Text trò chuyện xung quanh định dạng mã JSON, backend đã được cài đặt Regex Fallback để bắt chuỗi JSON ở tầng thấp nhất, ngăn chặn lỗi đứt gãy giữa chừng trong tiến trình.*
