# AGENTS.md — Cross-Tool AI Context

> File này được đọc bởi mọi AI coding agent (Claude, Cursor, Copilot, Antigravity/Gemini).

> Mục đích: Cung cấp context tối thiểu để AI hiểu project ngay lập tức.

## Project
**Agentic RAG Tư Vấn Học Vụ HCMUTE** — Chatbot hỏi đáp quy chế đào tạo cho sinh viên, dựa trên kiến trúc Agentic RAG với Intent Routing, Query Rewriting và Self-Correction Loop.

## Context Files
Đọc `.context/SUMMARY.md` trước. Chi tiết thêm trong `.context/ARCHITECTURE.md`, `.context/TECH_STACK.md`.

## Structure
```
backend/main.py          — FastAPI controller (POST /chat, GET /chat/history)
backend/llm_agent.py     — Agentic RAG core: key rotation, generator fallback, rewriter loop
backend/vector_store.py  — ChromaDB singleton loader + embedding model
backend/database.py      — SQLModel ORM (User, Conversation, ChatTurn)
frontend/app.py          — Streamlit chat interface
```

## Setup Commands
```bash
# Install
pip install -r requirements.txt

# Run backend
uvicorn backend.main:app --reload --port 8000

# Run frontend
streamlit run frontend/app.py
```

## Testing
```bash
# Verify imports
python -c "from backend.main import app; print('OK')"
```

## Coding Style
- **Language**: Python 3.10+
- **Comments**: Tiếng Việt
- **API responses**: JSON, tiếng Việt
- **Constants**: `_MODEL_*` prefixed, defined in `llm_agent.py`
- **Environment**: `.env` with `GROQ_API_KEY`, `GROQ_API_KEY_1..9`, `GEMINI_API_KEY`, `DATABASE_URL`

## Important Patterns
- **Key Rotation**: After rotating Groq API key, MUST call `_rebuild_all_chains()` — LangChain caches key at init time
- **Generator Fallback**: compound-mini → llama-70b (same key) → rotate key
- **`run_agentic_rag()`**: Core function reused in both API and Jupyter notebooks — changes here affect evaluation too

## Git Workflow (CRITICAL)
- TRƯỚC KHI commit bất cứ thứ gì, BẮT BUỘC phải đọc và chạy quy trình trong `.agent/skills/context-sync/SKILL.md`. Việc dùng `git diff` để tự động cập nhật thư mục `.context/` là quy định tối thượng của dự án này.

## Don'ts
- Do NOT hardcode API keys in source files
- Do NOT modify `vector_store.py` singleton pattern without updating `main.py` startup
- Do NOT change JSON output format of Router/Generator/Rewriter without updating Regex fallbacks in `llm_agent.py`
