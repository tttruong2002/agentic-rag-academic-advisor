# Agentic RAG Tư Vấn Học Vụ HCMUTE

> **KLTN — Kỹ Thuật Dữ Liệu, ĐH Công Nghệ Kỹ Thuật TP.HCM**

## Mục tiêu
Xây dựng Chatbot tư vấn học vụ cho sinh viên HCMUTE, dựa trên quy chế đào tạo & sổ tay sinh viên. Hệ thống dùng kiến trúc **Agentic RAG** với khả năng Intent Routing, Query Rewriting và Self-Correction Loop.

## Trạng thái hiện tại
- ✅ Backend FastAPI + Agentic RAG **hoạt động** trên VPS
- ✅ Frontend Streamlit **hoạt động** (sẽ chuyển ReactJS)
- ✅ ChromaDB với **6,655 vectors** từ 44 PDF nguồn
- ✅ PostgreSQL lưu lịch sử chat (SQLModel ORM)
- ✅ Evaluation: 150 câu hỏi benchmark, Naive RAG vs Agentic RAG
- 🔄 Data Pipeline đang cần nâng cấp (Gemini Files API thay Docling)

## Cấu trúc thư mục quan trọng
```
Code/
├── backend/           → FastAPI + Agentic RAG logic (4 files)
├── frontend/          → Streamlit chat UI (1 file)
├── notebooks/         → Data pipeline + Evaluation (5 notebooks)
├── data/              → raw PDFs, processed text, evaluation CSVs
├── chroma_db/         → Vector DB (124MB, 6 collections)
├── docs/              → Tài liệu dự án (BẠN ĐANG ĐỌC FILE NÀY)
├── .agents/skills/    → Agent Skills (community + custom)
├── AGENTS.md          → Cross-tool AI context
└── README.md          → GitHub-facing documentation
```

## Quy ước
- **Ngôn ngữ code**: Comments bằng tiếng Việt
- **API responses**: JSON format, tiếng Việt
- **Model naming**: Hằng số `_MODEL_*` trong `llm_agent.py`
- **Key rotation**: Groq API keys đánh số `GROQ_API_KEY`, `GROQ_API_KEY_1`, ... `GROQ_API_KEY_9`
- **Branch strategy**: `main` branch duy nhất (KLTN solo project)

## Files cần đọc thêm
- `ARCHITECTURE.md` — Sơ đồ kiến trúc và luồng xử lý
- `TECH_STACK.md` — Công nghệ và phiên bản
- `ROADMAP.md` — Lộ trình và To-Do
- `ADR.md` — Các quyết định kiến trúc (Architecture Decision Records)
- `docs/groq_api_issues_log.md` — Nhật ký chi tiết xử lý lỗi API Groq
