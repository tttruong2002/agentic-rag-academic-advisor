# Kế hoạch Dự án & Xử lý Vấn đề (Project Plan)

Văn bản này tổng hợp các vấn đề hiện đọng của hệ thống Agentic RAG Tư vấn Học vụ, đề xuất hướng giải quyết và thiết lập lộ trình phát triển (To-Do List) cùng thiết kế cơ sở dữ liệu cho giai đoạn tiếp theo.

---

## 1. Danh sách Vấn đề hiện tại & Giải pháp Đề xuất

### 1.1. Vấn đề Dữ liệu (ChromaDB)
Hệ thống truy xuất đang gặp khó khăn do chất lượng dữ liệu đầu vào (PDF) sau khi tiền xử lý bị phân mảnh và nhiễu:
- **Ngữ cảnh bị đứt gãy:** Một chunk đôi khi chỉ chứa nội dung mà thiếu đi Tiêu đề/Đề mục chính phân mảnh ở chunk trước đó.
- **Ký tự rác:** Trong quá trình tách trang, các thành phần định dạng tài liệu cố định (header, footer, số trang) bị trộn lẫn vào văn bản.
- **Bảng biểu vỡ cấu trúc:** Các file PDF chứa bảng scan và bảng biểu phức tạp không thể đọc chính xác bằng Docling hay UnstructuredPDFLoader truyền thống. Văn bản trích xuất ra vẫn còn lỗi nên phải đưa qua LLM để làm sạch thêm.

**💡 Giải pháp hiện tại đã áp dụng (Hybrid Extraction):**
Dùng kết hợp output của **Docling** + **UnstructuredPDFLoader**, sau đó đưa cả 2 kết quả raw đó vào **Gemini Flash API** để tổng hợp ra text thuần Việt hoàn chỉnh.

**💡 Định hướng mới — Dùng Gemini API làm PDF Parser chính:**
1. **Upload PDF trực tiếp lên Gemini API (Files API):** Bỏ qua hoàn toàn Docling/Unstructured. Gemini 2.5 Flash hỗ trợ **1 triệu token context** (đủ cho file 100+ trang), và có khả năng Vision để đọc cả trang scan, bảng biểu phức tạp.
2. **Xử lý theo Batch (tránh vượt Output Limit):** Giới hạn output của Gemini Flash là **~65K token/lần gọi**. Để an toàn, chia PDF thành các batch nhỏ (~10–20 trang/lần gọi), sau đó ghép kết quả lại.
3. **Chuẩn hóa Bảng biểu thành JSON Minified:** Yêu cầu Gemini trả bảng dưới dạng JSON 1 dòng (minified) để LLM hiểu cấu trúc chính xác, ví dụ: `{"headers":["Học phần","Số TC","Điều kiện"],"rows":[...]}`.
4. **Chunking theo Ngữ Nghĩa (Header Chunking):** Chuyển từ chia theo độ dài (Token/Char) sang `MarkdownHeaderTextSplitter`. Đảm bảo mỗi chunk luôn gắn với tiêu đề nguồn gốc trong Metadata.
5. **Context Caching:** Nếu cần gọi lại nhiều lần trên cùng nội dung PDF, sử dụng Gemini Context Caching để tiết kiệm chi phí đáng kể.

### 1.2. Vấn đề Rate Limit (Groq API) - [ĐÃ CẢI THIỆN]
Hệ thống sử dụng model `llama-3.3-70b-versatile` gặp lỗi `Error 429: Rate limit reached` do giới hạn TPM (Tokens Per Minute) của Groq ở ngưỡng 12K. Vòng lặp Agentic RAG gọi mô hình nhiều lần trong thời gian ngắn khiến hạn mức nhanh chóng cạn kiệt.

**💡 Giải pháp đề xuất:**
1. **Exponential Backoff:** Implement thư viện `Tenacity` trong Python ở hàm gọi LLM để hệ thống tự động Sleep (ngủ) một vài giây và thử lại nếu gặp mã HTTP 429.
2. **Đổi mô hình / Cung cấp:** Đổi sang model nhẹ hơn của Groq cho khâu Re-writer (llama 3.1 8b) hoặc nâng cấp API provider có quota rộng rãi hơn cho model Generator nếu có ngân sách.
3. **Caching (Semantic Cache):** Thêm bộ nhớ đệm (Redis / SQLite) để nếu User hỏi 1 câu tương tự câu vừa hỏi, trả về kết quả luôn thay vì nhờ LLM suy nghĩ lại từ đầu.

Hệ thống truy xuất đang gặp khó khăn do chất lượng dữ liệu đầu vào (PDF) sau khi tiền xử lý bị phân mảnh và nhiễu.
**💡 Trạng thái:** Đã hoàn thành bộ 150 câu hỏi thử nghiệm để bắt đầu đánh giá độ chính xác (Ground Truth).

**💡 Giải pháp đã triển khai:**
1. **Shuffle Key Rotation:** Ngẫu nhiên hóa thứ tự 10 API Keys giúp san sẻ gánh nặng TPM đều cho toàn bộ key ngay từ lúc khởi động.
2. **Robust Resume:** Coi điểm 0 là lỗi hệ thống, cho phép Notebook tự động chạy tiếp (Resume) tại đúng điểm lỗi thay vì chạy lại từ đầu.

### 1.3. Vấn đề UI/UX
Do định hướng dài hạn sẽ đập bỏ Streamlit và thay bằng **ReactJS** cho Frontend, nên việc chèn các tính năng tương tác phía FE lúc này (như Login Google) là không khả thi và gây dư thừa.

**💡 Giải pháp đề xuất:**
- Tạm ngưng các tính năng Auth trên giao diện Streamlit.
- Tập trung vào việc chuẩn hóa API Backend (`/v1/chat`, `/v1/auth`, `/v1/conversations`) để khi dựng xong ReactJS, chỉ cần "lắp ráp" thẳng vào.

---

## 2. Thiết kế Database Schema (PostgreSQL)

Để thay thế cho việc mất lịch sử chat mỗi lần refesh trang, ta sẽ dùng PostgreSQL. 
**Thư viện ORM đề xuất cho FastAPI:** **`SQLModel`**. Đây là thư viện do chính tác giả của FastAPI (Tiangolo) viết, kết hợp hoàn hảo giữa `SQLAlchemy` (ORM sức mạnh cao) và `Pydantic` (Data Validation). Nó mang lại trải nghiệm code DX (Developer Experience) sạch và mượt mà tương tự như `Prisma` bên Node.js.

### Schema Design (ERD Cơ bản)

#### **Table: `User`**
Lưu thông tin người dùng (Tạm thời chỉ mock 1 user mặc định).
- `id`: UUID (Primary Key)
- `username`: String (Unique) - vd: "Test User"
- `email`: String (Unique)
- `created_at`: Datetime
- `updated_at`: Datetime

#### **Table: `Conversation`**
Một User có thể tạo nhiều phiên chat (Session).
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> User.id)
- `title`: String (Tóm tắt tự động về ý chính của phiên chat, VD: "Hỏi đáp Thực tập Tốt nghiệp")
- `created_at`: Datetime
- `updated_at`: Datetime

#### **Table: `ChatTurn`**
Lưu từng dòng tin nhắn (Prompt của User, Answer của AI) thuộc về một phiên chat.
- `id`: UUID (Primary Key)
- `conversation_id`: UUID (Foreign Key -> Conversation.id)
- `user_query`: Text (Câu hỏi nguyên bản của sinh viên)
- `ai_reponse`: Text (Câu trả lời của AI)
- `turn_summary`: Text (Tóm tắt ngắn gộn của cặp hỏi-đáp này)
- `context_used`: Text (Văn bản được sử dụng để trả lời câu hỏi)
- `created_at`: Datetime

---

## 3. To-Do List (Hành động Tiếp theo)

- [ ] **Data Pipeline (Notebooks)**
  - [x] Trích xuất text thô bằng **Docling** + **UnstructuredPDFLoader** (Notebook `01_Raw_Extraction`).
  - [x] Dùng **Gemini Flash API** để làm sạch và hợp nhất text (Notebook `02_Refinement_Merge`).
  - [ ] **[MỚI] Viết Notebook `00_Gemini_PDF_Parser`:** Upload trực tiếp PDF lên Gemini Files API, xử lý theo batch ~10–20 trang/lần gọi, concat kết quả — thay thế toàn bộ pipeline cũ khi chất lượng đã kiểm chứng.
  - [ ] **[MỚI] Chuẩn hóa Bảng biểu → JSON Minified** trong prompt gửi Gemini để lưu vào ChromaDB chuẩn xác.
  - [ ] Viết lại logic Chunking theo `MarkdownHeaderTextSplitter` thay vì phân cắt theo độ dài.
  - [ ] Nạp lại toàn bộ data vào ChromaDB sau khi pipeline mới chạy ổn định.
- [ ] **Backend (FastAPI)**
  - [ ] Cài đặt PostgreSQL, cấu hình `.env` cho database URL.
  - [ ] Import `SQLModel`, định nghĩa các Models `User`, `Conversation`, `Message`.
  - [ ] Tạo module CRUD đơn giản và khởi tạo Database Migrations (`Alembic`).
  - [ ] Viết lại hàm xử lý API `/chat` để nhận tham số `conversation_id`, từ đó truy xuất lịch sử gần nhất nhét vào Context.
  - [ ] Thêm thư viện `tenacity` để bọc cơ chế Retry Retry-After / Exponential Backoff tránh lỗi Rate Limit.
- [ ] **Chuẩn bị chuyển đổi Frontend**
  - [ ] Thống nhất lại toàn bộ JSON Interface của Backend trả về.
  - [ ] Design kiến trúc React cơ bản cho việc hiển thị khung Chat.
