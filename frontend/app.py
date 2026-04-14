# frontend/app.py
import streamlit as st
import requests
import json

# Cấu hình trang
st.set_page_config(page_title="HCMUTE Chatbot", page_icon="🎓")

st.title("🎓 Trợ lý Quy chế Đào tạo HCMUTE")
st.markdown("Hỏi đáp về quy chế, sổ tay sinh viên dựa trên tài liệu nhà trường.")

# URL của Backend FastAPI
API_URL = "http://localhost:8000/chat"

# Sidebar: Tùy chỉnh Agentic RAG
with st.sidebar:
    st.header("⚙️ Tùy chỉnh Agentic")
    is_thinking = st.toggle("🧠 Chế độ Suy nghĩ (Thinking Mode)", value=False, help="Agent sẽ tự động suy luận lại và truy xuất mở rộng nhiều lần để tìm câu trả lời tốt nhất nếu lần đầu không đủ thông tin (Tối đa 3 lần).")

# Khởi tạo lịch sử chat từ Backend (chỉ chạy 1 lần lúc mới F5)
if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        # Gọi API lấy lịch sử chat
        res = requests.get("http://localhost:8000/chat/history")
        if res.status_code == 200:
            st.session_state.messages = res.json()
    except Exception as e:
        print(f"Không thể tải lịch sử: {e}")

# Hiển thị lịch sử chat cũ
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("context") and message.get("intent") == "RAG":
            with st.expander("📖 NỘI DUNG TÀI LIỆU ĐƯỢC TRUY VẤN (Context Gốc)"):
                st.code(message["context"], language='text')

# Xử lý input từ người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn ở đây..."):
    # 1. Hiển thị câu hỏi người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gọi API Backend
    with st.chat_message("assistant"):
        # Block status chỉ chứa logic gọi API và cập nhật trạng thái
        with st.status("Đang tra cứu và phân tích tài liệu...", expanded=True) as status:
            try:
                payload = {
                    "question": prompt,
                    "is_thinking": is_thinking
                }
                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    context = data.get("context", "")
                    intent = data.get("intent", "RAG")
                    retries = data.get("retries", 0)

                    if intent == "GREETING":
                        status.update(label="Đã hoàn thành phản hồi nhanh!", state="complete", expanded=False)
                    else:
                        if retries > 0:
                            status.update(label=f"Đã tra cứu và suy nghĩ {retries + 1} lần!", state="complete", expanded=False)
                        else:
                            status.update(label="Đã hoàn thành tra cứu!", state="complete", expanded=False)

                    # Lưu vào history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "context": context,
                        "intent": intent
                    })

                else:
                    answer = f"Lỗi server: {response.status_code} - {response.text}"
                    context = ""
                    intent = "ERROR"
                    retries = 0
                    status.update(label="Đã xảy ra lỗi!", state="error", expanded=True)
                    st.error(answer)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "context": "",
                        "intent": "ERROR"
                    })

            except requests.exceptions.ConnectionError:
                answer = "Không thể kết nối đến Backend. Hãy chắc chắn bạn đã chạy file `main.py`."
                context = ""
                intent = "ERROR"
                retries = 0
                status.update(label="Không thể kết nối đến Backend!", state="error", expanded=True)
                st.error(answer)
                st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "context": "",
                        "intent": "ERROR"
                })

        # ✔️ Câu trả lời được hiển thị ở ĐÂY, ngoài block st.status
        if intent not in ("ERROR",):
            st.markdown(answer)

        # Context chỉ hiển thị khi là RAG và có nội dung
        if context and intent == "RAG":
            with st.expander("📖 NỘI DUNG TÀI LIỆU ĐƯỢC TRUY VẤN (Context Gốc)"):
                st.code(context, language='text')

