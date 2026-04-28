# Architecture Decision Records (ADR)

## ADR-001: ChromaDB thay vì FAISS/Pinecone

**Ngày**: Khởi đầu dự án

**Trạng thái**: Accepted

**Bối cảnh**: Cần vector database cho RAG, yêu cầu: đơn giản, local, không tốn tiền.

**Quyết định**: Dùng ChromaDB PersistentClient (lưu file SQLite local).

**Lý do**:
- Zero cost (local, không cần server)
- API đơn giản, tích hợp tốt với LangChain
- Persistent trên disk, không mất data khi restart
- Đủ hiệu năng cho ~7K vectors

**Trade-off**: Không scale được cho production lớn (OK cho KLTN).

---

## ADR-002: Groq API thay vì OpenAI/Anthropic

**Ngày**: Khởi đầu dự án

**Trạng thái**: Accepted

**Bối cảnh**: KLTN hướng tới FREE cho sinh viên. GPT-4/Claude quá đắt.

**Quyết định**: Dùng Groq API (free tier) với Llama 3.1 và Compound models.

**Lý do**:
- Free tier với nhiều model mạnh (Llama 3.1 8B, 3.3 70B)
- Tốc độ inference cực nhanh nhờ LPU hardware
- Hỗ trợ JSON mode tốt

**Trade-off**: TPM thấp (6K-12K), cần Key Rotation để bù.

---

## ADR-003: Shuffle Key Rotation thay vì Paid Plan

**Ngày**: 14/04/2026

**Trạng thái**: Accepted

**Bối cảnh**: 1 key Groq free bị rate limit quá nhanh khi chạy Agentic loop.

**Quyết định**: Thu thập 10 free API keys, shuffle ngẫu nhiên lúc khởi tạo, round-robin khi gặp 429.

**Lý do**:
- Zero cost
- Tăng effective TPM lên ~10x
- Shuffle tránh luôn dùng key đầu tiên

**Bài học quan trọng**: LangChain ChatGroq bind cứng api_key lúc khởi tạo. SAU MỖI LẦN rotate key PHẢI gọi `_rebuild_all_chains()` để ép dùng key mới. Nếu không, xoay key vô nghĩa.

---

## ADR-004: Generator Fallback 2 tầng

**Ngày**: 14/04/2026

**Trạng thái**: Accepted

**Bối cảnh**: compound-mini đôi khi bị rate limit, cần fallback.

**Quyết định**: Thử compound-mini → Nếu limit → llama-3.3-70b (cùng key) → Nếu vẫn limit → Rotate sang key mới.

**Lý do**: Tận dụng tối đa quota của MỖI key trước khi chuyển key (2 model khác nhau có quota riêng trên cùng 1 key).

---

## ADR-005: SQLModel thay vì SQLAlchemy thuần / Prisma

**Ngày**: Khi thêm PostgreSQL

**Trạng thái**: Accepted

**Bối cảnh**: Cần ORM lưu lịch sử chat.

**Quyết định**: Dùng SQLModel (tác giả FastAPI viết).

**Lý do**:
- Kết hợp SQLAlchemy (ORM) + Pydantic (Validation) trong 1 class
- DX sạch, giống Prisma bên Node.js
- Tương thích tự nhiên với FastAPI dependency injection

---

## ADR-006: Dùng `.agent/skills/` chuẩn SKILL.md quốc tế

**Ngày**: 28/04/2026

**Trạng thái**: Accepted

**Bối cảnh**: Cần agent configuration mà mọi AI tool đều đọc được (Claude, Cursor, Copilot, Antigravity).

**Quyết định**: Dùng `.agent/skills/` thay vì `.agents/rules/` (Antigravity-only) hay `.cursor/rules/`.

**Lý do**:
- Chuẩn SKILL.md được hỗ trợ cross-tool (agentskills.io)
- Progressive disclosure: AI chỉ load skill khi cần, tiết kiệm token
- Version control: Git track được
- Kết hợp AGENTS.md ở root cho cross-tool context
