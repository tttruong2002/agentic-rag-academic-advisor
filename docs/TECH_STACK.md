# Tech Stack

## Runtime & Framework

| Layer | Technology | Vai trò |
|---|---|---|
| Language | Python ≥ 3.10 | Backend, Data Pipeline, AI |
| Backend Framework | FastAPI + Uvicorn | REST API server |
| Frontend | Streamlit | Chat UI (tạm thời, sẽ chuyển ReactJS) |
| ORM | SQLModel (SQLAlchemy + Pydantic) | Database models & validation |

## AI & LLM

| Vai trò | Model | Provider | Ghi chú |
|---|---|---|---|
| Embedding | `Alibaba-NLP/gte-multilingual-base` | Local CPU (HuggingFace) | Multilingual, normalize embeddings |
| Router | `llama-3.1-8b-instant` | Groq API | Tốc độ cao, phân luồng GREETING/RAG |
| Generator (chính) | `groq/compound-mini` | Groq API | Model compound với sub-models |
| Generator (dự phòng) | `llama-3.3-70b-versatile` | Groq API | Fallback khi compound-mini bị limit |
| Rewriter | `groq/compound` | Groq API | Viết lại query, tiếng Việt 100% |

## Database

| Database | Engine | Vai trò |
|---|---|---|
| Vector Search | ChromaDB (PersistentClient) + BM25 | 6,655 embeddings, 6 collections, Hybrid Search (Dense + Sparse) |
| SQL (Chat History) | PostgreSQL | User, Conversation, ChatTurn |

## Data Pipeline

| Bước | Công cụ | File |
|---|---|---|
| PDF Extraction | Docling + UnstructuredPDFLoader | `notebooks/legacy/01_Raw_Extraction.ipynb` |
| Text Refinement | Gemini Flash API | `notebooks/legacy/02_Refinement_Merge.ipynb` |
| Evaluation (Naive) | Groq compound-mini, 150 Qs | `notebooks/04_Evaluation_Naive_RAG.ipynb` |
| Evaluation (Agentic) | Groq + Resume/Retry logic | `notebooks/05_Evaluation_Agentic_RAG.ipynb` |

## Key Libraries (requirements.txt)

```
streamlit, python-dotenv, langchain, langchain-groq, chromadb,
sentence-transformers, langchain-core, langchain-docling,
psycopg2-binary, langchain_huggingface, langchain_chroma,
fastapi, uvicorn, pydantic, sqlmodel
```

## API Keys & Environment

| Key | Mục đích |
|---|---|
| `GROQ_API_KEY` + `GROQ_API_KEY_1..9` | 10 keys xoay vòng cho Groq |
| `GEMINI_API_KEY` | Google Gemini Flash (Data Pipeline) |
| `DATABASE_URL` | PostgreSQL connection string |
