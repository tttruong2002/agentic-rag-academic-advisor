# Nhật ký vấn đề (Issue Log): Giới hạn API của Groq và Lỗi 413/429

Tài liệu này được ghi chú lại quá trình debug nhằm giải quyết các lỗi giới hạn tài nguyên (Rate Limit & Entity Too Large) trên tập API Free-tier của Groq trong suốt quá trình xây dựng hệ thống Agentic RAG. Nó phục vụ làm bài học kinh nghiệm phát triển cũng như phòng tránh hiện tượng tương tự khi chuyển sang các Endpoint nội bộ khác.

## 1. Bản chất của các Endpoint "Agentic AI" (groq/compound)
- **Tình trạng ban đầu:** Hệ thống đổi sang Endpoint `groq/compound` hoặc `groq/compound-mini` và liên tục đối mặt với lỗi `413 Request Entity Too Large` dù chuỗi Query (Context + Question) chỉ nằm trong ngưỡng rất ngắn (~1200 Tokens), khác hoàn toàn so với thông số Context Window do Groq cung cấp trên web (131,072 Tokens).
- **Nguyên nhân cốt lõi (Phát hiện thông qua Script check Rate Limits):** 
  - `groq/compound` không phải là một Model lõi đơn thuần như Llama-3 hay Mixtral. Nó là tên định danh ảo cho một **Đường ống hệ thống đa mô hình (Agentic Pipeline)** nằm trong máy chủ của Groq.
  - Khi gọi Endpoint này, Groq sẽ tự động đẩy luồng Request đi qua nhiều model con (Sub-models) để phục vụ cho tool-calling, check safety, vv.
  - Vấn đề là: Một trong số những Model ngầm định này của Groq (ví dụ như `openai/gpt-oss-120b` hoặc các safety filters siêu siêu nhỏ như `llama-prompt-guard`) có **Giới hạn Rate Limit hoặc Context Windows cực kỳ thấp (Ví dụ chỉ 512, 1024 token hoặc thấp hơn)**!
  - Việc body của chúng ta (dù chỉ mới 1251 token) lọt qua cửa chính, bị vấp ngay tại cái van xả của Model filter ngầm này (vốn chỉ ôm được 1024 chữ), khiến nguyên hệ thống Compound của Groq sụp đổ và phun ra mã lỗi 413: _Request quá cỡ_.

## 2. Vấn đề Parse PDF Table trùng lặp (Nguyên nhân Context Phình to một cách bất thường)
- **Tình trạng:** Khi chạy debug, Context String tạo cảm giác cực kỳ dài vì bên trong ngập tràn những chuỗi lặp lại như _"Hai học phần Giáo dục thể chất 2 và 3 (Sinh viên chọn...)"_.
- **Nguyên nhân:** Lỗi cơ bản từ quá trình sử dụng các thư viện trích xuất PDF (ví dụ PyPDF) xử lý Bảng biểu (Tables). Khi parse một bảng biểu dài nhưng ô Text nằm dính hoặc bị trộn ô, thuật toán ngắt dòng đã append cứng nội dung của 1 ô trộn vào TẤT CẢ CÁC DÒNG của Table đó. Do tính rườm rà này, quá trình nhúng dữ liệu đem nguyên cục rác "nhân bản vô tính" bỏ vào DB.
- **Biện pháp khuyên dùng (nếu có thời gian vọc lại Data):** Cần tinh chỉnh file xử lý dữ liệu thô `01_Raw_Extraction.ipynb` bằng cách xài thư viện chia bảng mạnh mẽ hơn (Ví dụ sử dụng OCR Model hoặc Camelot cho PDF Table).

## 3. Kiến trúc Key Rotation + 2-Tier Fallback
Do hệ thống Free-tier của Groq có Tokens-per-minute (TPM) quá thấp (6,000 - 12,000 TPM tuỳ model lõi), giải pháp khắc phục bằng logic đã được hệ thống thêm vào backend `llm_agent.py`:
- **Quay Vòng API Key (Round-robin):** Duy trì danh sách 9 key Groq. Khi một Key dính lỗi Rate Limit, hàm `_rotate_key` tự động trỏ sang key mới. **Bắt buộc** phải có hàm `_rebuild_all_chains` ngay sau khi Rotate để ép framework Langchain xoá cache Key cũ nạp Key mới vào lại Prompt Pipeline.
- **Tầng Fallback (Compound Main -> Compound Mini):** Giúp duy trì mạch trả lời của hệ thống, tuy nhiên cần lưu ý về cấu trúc của Endpoint Groq Mini như đã nói ở Phân đoạn 1. Phù hợp nhất vẫn là dùng model Llama gốc (`llama-3.1-8b` hay `llama-3.3-70b-versatile`) không qua các sub-models để tránh tắc nghẽn vô cớ.

## 4. Ghi chú cho Evaluation (Jupyter Notebook `04` & `05`)
- Notebook Đánh giá đòi hỏi cần chạy một lượng lớn truy vấn liên tục (150 Câu). Điều này có nguy cơ tiêu tốn TPM khổng lồ.
- Hướng tiếp cận hợp lý hiện tại là sử dụng loại Model nào thuần tuý (như `groq/compound-mini` nếu nó chạy ổn ở mức Tokens ít) hoặc quay về model lõi.
- Tuyệt đối nên giữ vững cơ chế Key Rotation ngay chính bên trong các Notebook Evaluation (hoặc pass qua Function chung trong `llm_agent.py`) để các Notebook chạy không bị đứt đoạn gãy đổ giữa chừng (vốn làm tốn công chạy lại suốt 3 tiếng).
