# Agentic RAG Academic Advisor

> **Capstone Project (KLTN)** — Ho Chi Minh City University of Technology and Engineering (HCMUTE)
> Major: Data Engineering

An **Agentic RAG-based chatbot** for retrieving academic policy documents and providing automated advisory services to students. The system leverages **Intent Routing**, **Query Rewriting**, and a **Self-Correction loop** to deliver accurate, context-aware answers from the university's academic handbook.

---

## ✨ Key Features

- **Intent Routing**: Automatically distinguishes between casual conversation (GREETING) and policy-related queries (RAG) — skipping the database for small talk.
- **Self-Correction Loop**: If the retrieved context is insufficient, the system rewrites the query via a **Rewriter Agent** and retries retrieval up to N times.
- **Thinking Mode**: A frontend toggle that enables deeper retry loops (max 3 attempts) for complex questions.
- **Persistent Chat History**: Conversation sessions and message turns are saved to **PostgreSQL** via SQLModel ORM.
- **Hybrid Data Pipeline**: PDF source documents (including scanned pages and complex tables) are extracted using **Docling** + **UnstructuredPDFLoader**, then refined and cleaned using **Gemini Flash API** to produce high-quality Vietnamese plain text for vectorization.

---

## 🏗️ Architecture

```
User (Browser)
    │
    ▼
[Frontend — Streamlit]    ←── app.py
    │  /chat (HTTP)
    ▼
[Backend — FastAPI + Uvicorn]
    ├── main.py           (API Controller)
    ├── llm_agent.py      (Agentic RAG Logic, Chains, Prompts)
    ├── vector_store.py   (ChromaDB loader + Embedding Model)
    └── database.py       (SQLModel ORM — PostgreSQL)
    │
    ├──► ChromaDB (local vector store)
    └──► PostgreSQL (chat history: User, Conversation, ChatTurn)
```

### LLM & Embedding Models

| Role | Model | Provider |
|---|---|---|
| Embedding | `Alibaba-NLP/gte-multilingual-base` | Local CPU |
| Router & Rewriter | `llama-3.1-8b-instant` | Groq API |
| Generator | `groq/compound-mini` | Groq API |

---

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py               # FastAPI app & endpoints
│   ├── llm_agent.py          # Core Agentic RAG logic
│   ├── vector_store.py       # ChromaDB & embedding loader
│   └── database.py           # PostgreSQL ORM models (SQLModel)
├── frontend/
│   └── app.py                # Streamlit chat interface
├── notebooks/
│   ├── legacy/
│   │   ├── 01_Raw_Extraction.ipynb   # PDF extraction pipeline (Legacy)
│   │   ├── 02_Refinement_Merge.ipynb # Text refinement & vectorization (Legacy)
│   |   └── 03_Evaluation_RAG.ipynb       # Baseline RAG evaluation
│   ├── 04_Evaluation_Naive_RAG.ipynb # Naive RAG eval (compound-mini, 150 Qs)
│   └── 05_Evaluation_Agentic_RAG.ipynb # Agentic RAG comparison
├── data/
│   ├── raw/                  # Original PDF source files (in .gitignore)
│   ├── processed/            # Cleaned plain-text documents
│   └── evaluation/           # Benchmark questions (150questions.txt)
├── chroma_db/                # Local ChromaDB vector store (in .gitignore)
├── requirements.txt
├── .env.example              # Environment variable template
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** >= 3.10
- **PostgreSQL** (running locally or via Docker)
- API Keys: **Groq**, **Google Gemini** (for data pipeline)

### 1. Clone the repository

```bash
git clone https://github.com/tttruong2002/agentic-rag-academic-advisor.git
cd agentic-rag-academic-advisor
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Required keys in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/your_db_name
```

### 5. Initialize the database

```bash
# Run the FastAPI server once to auto-create tables via SQLModel
uvicorn backend.main:app --reload
```

### 6. Build the vector database

Run the Jupyter Notebooks in order (found in `notebooks/legacy/` or your new pipeline notebooks):

```
notebooks/legacy/01_Raw_Extraction.ipynb  →  notebooks/legacy/02_Refinement_Merge.ipynb
```

This generates the `chroma_db/` folder automatically.

### 7. Run the application

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`.

---

## 📊 Evaluation

Evaluation notebooks benchmark the system using **150 academic policy questions**:

| Notebook | Description |
|---|---|
| `notebooks/legacy/03_Evaluation_RAG.ipynb` | Baseline RAG (early version) |
| `notebooks/04_Evaluation_Naive_RAG.ipynb` | Naive RAG with `compound-mini` on 150 Qs |
| `notebooks/05_Evaluation_Agentic_RAG.ipynb` | Agentic RAG vs Naive RAG comparison |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI, Uvicorn |
| Vector DB | ChromaDB |
| SQL DB | PostgreSQL + SQLModel |
| LLM API | Groq (Llama 3.1), Google Gemini Flash |
| Embeddings | sentence-transformers (HuggingFace) |
| Data Pipeline | Docling, LangChain, Jupyter Notebooks |

---

## ⚠️ Notes

- The `chroma_db/` directory is excluded from version control (`.gitignore`). You must rebuild it locally by running the data pipeline notebooks.
- The `.env` file is **never committed**. Use `.env.example` as a reference.
- PDF source documents in `data/raw/` are **not included** in this repository due to copyright restrictions.
