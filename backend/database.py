# backend/database.py
import os
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Session, create_engine
import uuid

# Lấy URL kết nối CSDL từ biến môi trường (File .env)
# Nếu chưa thiết lập, ta dùng địa chỉ mặc định của Postgres local
DATABASE_URL = os.getenv("DATABASE_URL")

# Khởi tạo Engine (Động cơ kết nối CSDL của SQLAlchemy tích hợp trong SQLModel)
engine = create_engine(DATABASE_URL, echo=False)

# -------------------------------------------------------------------
# ĐỊNH NGHĨA CÁC BẢNG (TABLES) TRONG DATABASE
# Mỗi Class đại diện cho 1 Bảng. Các thuộc tính là Cột.
# Cách làm này của Python (SQLModel) giống với Prisma Schema!
# -------------------------------------------------------------------

class User(SQLModel, table=True):
    # Field(default_factory=uuid.uuid4) giúp tự tạo ID ngẫu nhiên mỗi khi có User mới
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id") # Liên kết khóa ngoại tới bảng User
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatTurn(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id") # Liên kết tới Conversation
    user_query: str
    ai_response: str
    
    # Optional[str] nghĩa là cột này có thể chứa giá trị Null
    turn_summary: Optional[str] = None
    context_used: Optional[str] = None 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# -------------------------------------------------------------------
# HÀM HỖ TRỢ (CONNECTION CONTROLLER)
# -------------------------------------------------------------------

def create_db_and_tables():
    """
    Hàm này dùng để TỰ ĐỘNG tạo ra toàn bộ các bảng trên trong Postgres.
    Nó sẽ đối chiếu, nếu bảng chưa có thì tạo, có rồi thì bỏ qua.
    Rất NHANH cho giai đoạn phát triển, không cần xài Migration (Alembic) rườm rà.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Hàm trả về 1 phiên làm việc với DB. 
    Các Endpoint của FastAPI sẽ mượn Session này để query, sau đó tự đóng khi xong việc.
    """
    with Session(engine) as session:
        yield session
