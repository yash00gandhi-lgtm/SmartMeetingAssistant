---
title: Smart Meeting Assistant
emoji: 📝
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 📝 Smart Meeting Assistant

A FastAPI + LangChain (LCEL) app that turns meeting notes into:

- 📋 **Summary** — what was discussed
- ✅ **Action Items** — who does what by when
- ❓ **Follow-up Questions** — for the next meeting
- ➡️ **Next Steps** — concrete things to do
- 🔍 **RAG Search** — ask questions across all past meetings
- ⬇️ **Export** — download all results as `.txt`

Accepts **raw text or PDF** input. Stores every meeting in ChromaDB for semantic search.

**Stack:** FastAPI · LangChain LCEL · ChromaDB · OpenRouter/Groq · sentence-transformers · vanilla HTML/CSS/JS · Docker

---

## 📁 Project Structure

```
smart-meeting-assistant/
├── main.py               # FastAPI app + endpoints
├── config.py             # .env loader
├── llm_provider.py       # OpenRouter / Groq factory
├── meeting_loader.py     # text or PDF input
├── vector_store.py       # ChromaDB layer
├── chains.py             # 5 LCEL chains (summary, actions, etc.)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── uploads/              # uploaded PDFs (auto)
├── chroma_db/            # vector DB (auto)
├── exports/              # exported .txt files (auto)
├── requirements.txt
├── .env / .env.example / .gitignore
├── Dockerfile / .dockerignore
└── README.md
```

---

## 🧩 API Endpoints

| Method | Endpoint            | What it does |
|--------|---------------------|--------------|
| GET    | `/health`           | Health check |
| POST   | `/process-meeting`  | Accept notes (text or PDF), run all 4 chains, store in DB |
| POST   | `/search`           | RAG Q&A across past meetings |
| GET    | `/meetings`         | List all stored meetings |
| POST   | `/export`           | Save processed meeting as `.txt` and download |

Interactive docs: `http://localhost:8000/docs`

---

## 🚀 Setup (VS Code, Windows)

### 1. Python 3.10+ + a virtual env
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install deps (langchain pinned to 0.3.x — avoids v1 import breaks)
```powershell
pip install --upgrade pip
pip install -r requirements.txt --timeout 120 --retries 10
```

### 3. Add your API key
Open `.env` and paste your `OPENROUTER_API_KEY` (free from <https://openrouter.ai>).
Or switch `LLM_PROVIDER=groq` to use your Groq key.

### 4. Run
```powershell
uvicorn main:app --reload --port 8000
```

Open <http://localhost:8000>.

---

## 🐳 Docker

```bash
docker build -t smart-meeting-assistant .
docker run --env-file .env -p 8000:8000 \
  -v "$(pwd)/uploads:/app/uploads" \
  -v "$(pwd)/chroma_db:/app/chroma_db" \
  -v "$(pwd)/exports:/app/exports" \
  smart-meeting-assistant
```

---

## 🔁 Working Flow

```
1. User pastes notes / uploads PDF + title  →  POST /process-meeting
2. Backend loads text (PyPDFLoader if PDF)
3. Runs 4 LCEL chains in parallel-ish:
   summary_chain | action_items_chain | follow_up_chain | next_steps_chain
4. Stores the meeting in ChromaDB with metadata {meeting_id, title, date}
5. Returns all 4 outputs to the UI
6. User can:
   - Export results as .txt   (POST /export)
   - Search past meetings     (POST /search → RAG)
   - List all meetings        (GET  /meetings)
```

---

## 🛠️ Common Issues

| Problem | Fix |
|--------|-----|
| `cannot import name 'create_tool_calling_agent'` | langchain v1 is incompatible — `pip install 'langchain<1.0.0'` |
| `OPENROUTER_API_KEY is empty` | Add to `.env`, restart server |
| First request very slow | Embedding model downloads on first use (~80 MB) |
| OpenRouter rate-limited | Set `LLM_PROVIDER=groq` in `.env` |
| PDF extracts empty text | Probably scanned PDF — needs OCR (future work) |

---

## 🔒 Security
`.env` is in `.gitignore`. Never commit real keys. Rotate immediately if leaked.
