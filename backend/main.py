# backend/main.py
import sys
import os
# Đảm bảo Python hiểu thư mục gốc là 'Code' (thư mục cha của 'backend') khi chạy bằng `python backend/main.py`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vá lỗi encode Emoji trên Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

# 1. Setup Environment - PHẢI LOAD TRƯỚC TIÊN!
from dotenv import load_dotenv
load_dotenv(override=True)

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Import các components Tách Nhỏ
from sqlmodel import Session, select
from backend.database import create_db_and_tables, get_session, User, Conversation, ChatTurn
from backend.llm_agent import init_agents, run_agentic_rag
from backend.vector_store import get_retriever # ghi đè để có thể cập nhật .env mới nhất

app = FastAPI(title="HCMUTE Chatbot API")

class ChatRequest(BaseModel):
    question: str
    is_thinking: bool = False

class ChatResponse(BaseModel):
    answer: str
    context: str
    intent: str
    retries: int

class HistoryResponse(BaseModel):
    role: str
    content: str
    context: str
    intent: str

@app.on_event("startup")
def startup_event():
    """ Khởi động các Module Tách Rời """
    print("⏳ [Main] Bắt đầu khởi tạo hệ thống...")
    init_agents()           # Tự load Model + Prompts bên tệp llm_agent
    create_db_and_tables()  # Tự động kết nối Postgres và tạo 3 Bảng nếu chưa có
    print("✅ [Main] API backend đã sẵn sàng nhận kết nối.")
    get_retriever()         # Tải Embedding Model và liên kết ChromaDB lên RAM ngay khi Startup

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_session)):
    """API Agentic xử lý câu hỏi với Self-Correction và Lưu Postgres"""
    
    question = request.question
    max_retries = 3 if request.is_thinking else 1

    # ==========================================================
    # 1. Gọi Hàm Cốt Lõi Agentic RAG
    # ==========================================================
    final_answer, accumulated_context, intent, retries = run_agentic_rag(
        question=question, 
        max_retries=max_retries
    )
    
    # ==========================================================
    # 2. Xử lý Database - Lưu Lịch Sử (Hướng dẫn cách dùng ORM)
    # ==========================================================
    try:
        # Bước A: Tìm hoặc tạo 1 tài khoản (do chưa có log-in)
        user = db.exec(select(User).where(User.username == "Test User")).first()
        if not user:
            user = User(username="Test User", email="test@student.hcmute.edu.vn")
            db.add(user) # <- Giống prisma.user.create()
            db.commit()
            db.refresh(user)
            
        # Bước B: Tìm hoặc tạo 1 Phiên chat mặc định cho User này
        conv = db.exec(select(Conversation).where(Conversation.user_id == user.id)).first()
        if not conv:
            conv = Conversation(user_id=user.id, title="Phiên Hỏi Đáp Mặc Định")
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # Bước C: Ghi log dòng Chat vừa xong vào Bảng ChatTurn
        chat_turn = ChatTurn(
            conversation_id=conv.id,
            user_query=question,
            ai_response=final_answer,
            context_used=accumulated_context
        )
        db.add(chat_turn)
        db.commit()
        print("✅ [DB] Log lịch sử chat đã được ghi xuống Postgres!")
        
    except Exception as e:
        print("❌ [DB] Lưu Postgres thất bại, hãy check lại file .env chứa Mật khẩu DB! Lỗi:", e)
        
    # ==========================================================
    # 3. Trả kết quả về cho Frontend Streamlit (Như cũ)
    # ==========================================================
    return ChatResponse(
        answer=final_answer,
        context=accumulated_context,
        intent=intent,
        retries=retries
    )

@app.get("/chat/history", response_model=list[HistoryResponse])
def get_chat_history(db: Session = Depends(get_session)):
    """API Load 10 lượt chat gần nhất của Test Chat Session"""
    user = db.exec(select(User).where(User.username == "Test User")).first()
    if not user:
        return []
    conv = db.exec(select(Conversation).where(Conversation.user_id == user.id)).first()
    if not conv:
        return []
    
    # Lấy 10 Turn mới nhất (Đảo ngược để hiển thị từ cũ tới mới trên UI)
    turns = db.exec(
        select(ChatTurn)
        .where(ChatTurn.conversation_id == conv.id)
        .order_by(ChatTurn.created_at.desc())
        .limit(10)
    ).all()
    
    turns.reverse()
    
    history = []
    for t in turns:
        # Mỗi Turn gồm 1 tin nhắn User và 1 tin nhắn AI
        history.append({
            "role": "user",
            "content": t.user_query,
            "context": "",
            "intent": "UNKNOWN"
        })
        history.append({
            "role": "assistant",
            "content": t.ai_response,
            "context": t.context_used or "",
            "intent": "RAG" if t.context_used else "GREETING"
        })
        
    return history

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

