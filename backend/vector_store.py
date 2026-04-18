# backend/vector_store.py
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb

# Cấu hình cứng đường dẫn DB (bạn có thể đưa vào .env nếu muốn)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Nhảy ngược ra ngoài backend 1 bậc để tìm thư mục `chroma_db`
DB_PATH = os.path.join(BASE_DIR, "..", "chroma_db") 
FINAL_COLLECTION = "academic_regulations"
EMBEDDING_MODEL_NAME = "Alibaba-NLP/gte-multilingual-base"

# Tạo một biến cache để lưu kết quả, tránh việc load lại nặng nề mỗi lần gọi request
_retriever_instance = None

def get_retriever():
    """ 
    Hàm này dùng để khởi tạo kết nối với Chroma (Vector Search).
    Chỉ chạy đúng 1 lần duy nhất khi ứng dụng FastAPI bật lên (Startup Event)
    """
    global _retriever_instance
    if _retriever_instance is not None:
        return _retriever_instance
        
    print("⏳ [VectorStore] Đang khởi tạo Embedding Model (CPU)...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
        encode_kwargs={'normalize_embeddings': True}
    )

    print(f"⏳ [VectorStore] Đang kết nối ChromaDB tại: {DB_PATH}")
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    vector_store = Chroma(
        client=chroma_client,
        collection_name=FINAL_COLLECTION,
        embedding_function=embedding_model
    )
    
    # Thiết lập chỉ lấy top k = 5 tài liệu sát ngữ nghĩa nhất
    _retriever_instance = vector_store.as_retriever(search_kwargs={'k': 5})
    return _retriever_instance

def format_context(docs):
    """ 
    Tiện ích dọn dẹp các Docs thô thành 1 đoạn văn String sạch sẽ 
    rồi nhét vào Context của LLM thay vì bắt API Groq đọc đống rác JSON metadata.
    """
    context_parts = []
    for i, doc in enumerate(docs):
        # Không cần lấy filename từ metadata vì trong nội dung đã có
        part = f"--- NGUỒN #{i+1} ---\n{doc.page_content}\n"
        context_parts.append(part)
    return "\n".join(context_parts)
