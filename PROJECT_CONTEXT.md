# Ngữ cảnh dự án: Nâng cao hiệu quả hệ thống tư vấn học vụ bằng kiến trúc Agentic RAG kết hợp kỹ thuật tìm kiếm lai (Khóa luận tốt nghiệp ngành Kỹ thuật dữ liệu)

## Tổng quan
Dự án là một hệ thống Chatbot tư vấn học vụ dành cho sinh viên trường Đại học Công nghệ Kỹ thuật TP.HCM (HCMUTE), dựa trên quy chế đào tạo và sổ tay sinh viên.
Hệ thống hiện tại đã được nâng cấp lên cấu trúc **Agentic RAG** với khả năng định tuyến ý định (Intent Routing), viết lại truy vấn (Query Rewriting), và tự kiểm lỗi (Self-Correction).

## Kiến trúc hiện tại (Agentic RAG)
1. **Frontend**: Xây dựng bằng `Streamlit` (`frontend/app.py`). Có giao diện chat, tích hợp thanh trạng thái (`st.status`) thể hiện tiến trình suy nghĩ của AI.
   - Hỗ trợ nút **Chế độ Suy nghĩ (Thinking Mode)**, cho phép Agent retry tối đa 3 lần nếu context ban đầu chưa cung cấp đủ dữ kiện.
2. **Backend**: Xây dựng bằng `FastAPI` với cấu trúc Moduler phân tách rõ ràng (chuẩn bị cho mở rộng React):
   - `backend/main.py`: Controller chính chạy server Uvicorn và API endpoint. Tích hợp SQLModel lưu lịch sử chat.
   - `backend/database.py`: Quản lý Database ORM (SQLModel) liên kết PostgreSQL lưu lịch sử Chat(`User`, `Conversation`, `ChatTurn`).
   - `backend/llm_agent.py`: Service chứa logic các Chains Mô hình Groq, Prompts, Hàm lõi tự sửa lỗi `run_agentic_rag`.
   - `backend/vector_store.py`: Tách riêng phần load ChromaDB và tài nguyên Nhúng dữ liệu (Embedding Model CPU).
   - **Cơ chế Xoay vòng Key (Shuffle Key Rotation)**: Ngẫu nhiên hóa danh sách API Key tại thời điểm khởi tạo để cân bằng tải (Load Balancing) và tối đa hóa TPM/RPM.
3. **Database**: 
   - Vector Search: `ChromaDB` cục bộ tại thư mục `chroma_db`.
   - Database SQL: `PostgreSQL` quản lý lịch sử hỏi đáp.
4. **Mô hình (LLM & Embeddings)**:
   - **Embedding**: `Alibaba-NLP/gte-multilingual-base` (chạy trên CPU cục bộ).
   - **Agent Router**: `llama-3.1-8b-instant` (tốc độ cao để phân luồng ý định).
   - **Agent Rewriter**: `groq/compound` (đủ tốt và promt ưu tiên tiếng Việt 100%).
   - **Agent Generator**: `groq/compound-mini` (Chính) và `llama-3.3-70b-versatile` (Dự phòng khi chính limit).
## Luồng xử lý dữ liệu tiền kỳ (Data Pipeline)
Dự án bao gồm các file Jupyter Notebook để xử lý dữ liệu và đánh giá:
- `01_Raw_Extraction.ipynb`: Trích xuất dữ liệu gốc dạng thô từ PDF hoặc tài liệu thô.
- `02_Refinement_Merge.ipynb`: Tinh chỉnh dữ liệu text, chia đoạn (chunking), gom nhóm chuẩn bị vector hóa. (Kết quả có xuất ra text `merged_documents.txt`).
## Đánh giá (Evaluation)
- `150questions.txt`: Bộ 150 câu hỏi benchmark chính thức (bổ sung thêm 100 câu mới).
- `03_Evaluation_RAG.ipynb`: Thử nghiệm mô hình RAG ban đầu (cũ).
- `04_Evaluation_Naive_RAG.ipynb`: Đánh giá RAG cơ bản (Baseline).
- `05_Evaluation_Agentic_RAG.ipynb`: Đánh giá Agentic RAG với cơ chế **Robust Resume** (coi `score=0` là flag để Resume) và **Flexible Re-generation** (Empty answer = Re-run).
- **Judge Robustness**: Tích hợp Regex Fallback và Debug Logging chi tiết để bóc tách JSON từ kết quả chấm điểm.

## Luồng Backend RAG Agentic (Hoạt động thực tế)
Hệ thống API `/chat` gồm 2 bước chính:

**1. Intent Routing (Phân luồng ý định)**
- Nhận `question` từ user, đi qua `llm_router`.
- Nếu Intent là **GREETING** (giao tiếp thông thường, hỏi thăm bản thân AI): Trả về kết quả giao tiếp ngay, bỏ qua CSDL.
- Nếu Intent là **RAG** (tìm thông tin nghiệp vụ/quy chế): Bắt đầu vòng lặp truy xuất dữ liệu.
- **Logging cải tiến**: Khi Router gặp lỗi, nội dung payload (nếu có) sẽ được in ra để hỗ trợ debug.

**2. Self‑Correction Loop (RAG + Rewriter)**
- Prompt Caching: static prefix (vai trò, quy tắc, JSON mẫu) được đưa lên đầu, chỉ `{context}` và `{question}` là phần động.
- Nhúng `current_query` (vòng 1 là câu hỏi gốc) và gọi `retriever` lấy top chunks tài liệu.
- Generator xử lý và ép cấu trúc output sang dạng hàm JSON: `{"is_found": true/false, "answer": "..."}`.
- Nếu `is_found == true`: Tìm thấy thông tin, thoát vòng lặp và trả về cho Client.
- Nếu `is_found == false`: Context không đủ để giải đáp.
  - Khi đó, hệ thống sẽ gọi **Rewriter Agent** sinh ra `rewritten_query` mới tinh chỉnh từ câu hỏi cũ và các từ viết tắt học vụ (dktc, kltn...).
  - Vòng lặp RAG sẽ xoay vòng với `current_query` mới (số lần lặp tối đa phụ thuộc cờ `is_thinking`).
  
*Lưu ý: Để đối mặt với việc các model mở (Llama 3.1) thỉnh thoảng sinh Text trò chuyện xung quanh định dạng mã JSON, backend đã được cài đặt Regex Fallback để bắt chuỗi JSON ở tầng thấp nhất, ngăn chặn lỗi đứt gãy giữa chừng trong tiến trình.*

## Tài liệu bổ sung
- `docs/groq_api_issues_log.md`: Nhật ký chi tiết xử lý lỗi API Groq.
- `project_plan.md`: Lộ trình và trạng thái các đầu việc (To-Do).
