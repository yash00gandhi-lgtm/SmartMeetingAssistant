"""
main.py
-------
FastAPI app exposing:

  GET  /health           -> health check
  POST /process-meeting  -> ingest meeting notes (text OR PDF)
                            -> run all 4 chains in parallel
                            -> store the meeting for future search
  POST /search           -> search across past meetings (RAG)
  GET  /meetings         -> list all stored meetings
  POST /export           -> export a processed meeting as a .txt file

The frontend (HTML/CSS/JS) is served from /frontend.
"""

import os
import uuid
import shutil
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import UPLOAD_DIR, EXPORT_DIR
from meeting_loader import load_from_pdf, load_from_text
from vector_store import store_meeting, list_meetings, get_meeting
from chains import (
    summary_chain,
    action_items_chain,
    follow_up_chain,
    next_steps_chain,
    search_qa_chain,
)

# ---------------- App ----------------
app = FastAPI(
    title="Smart Meeting Assistant",
    description="Process meeting notes: summary, action items, follow-ups, next steps. Search past meetings via RAG.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Request models ----------------
class SearchRequest(BaseModel):
    question: str


class ExportRequest(BaseModel):
    meeting_id: str
    title: str
    summary: str
    action_items: str
    follow_ups: str
    next_steps: str


# ---------------- Endpoints ----------------

@app.get("/health")
def health():
    return {"status": "ok", "message": "Smart Meeting Assistant is running"}


@app.post("/process-meeting")
async def process_meeting(
    title: str = Form(...),
    notes_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Accept meeting notes either as raw text OR as a PDF file.
    Then run all 4 chains and store the meeting in ChromaDB.

    Form fields:
      title       — meeting title (required)
      notes_text  — pasted text (optional if file is provided)
      file        — PDF file (optional if notes_text is provided)
    """
    # ---- 1) Load notes from whichever input was given ----
    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            notes = load_from_pdf(save_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF read failed: {e}")
    elif notes_text:
        notes = load_from_text(notes_text)
    else:
        raise HTTPException(status_code=400, detail="Provide either notes_text or a PDF file")

    if not notes:
        raise HTTPException(status_code=400, detail="No text could be extracted")

    # ---- 2) Run the 4 LCEL chains ----
    # Each chain is independent. We run them sequentially for simplicity;
    # in production you could use asyncio.gather for parallel calls.
    inputs = {"notes": notes}
    try:
        summary = summary_chain.invoke(inputs)
        action_items = action_items_chain.invoke(inputs)
        follow_ups = follow_up_chain.invoke(inputs)
        next_steps = next_steps_chain.invoke(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain failed: {e}")

    # ---- 3) Store the meeting for future RAG search ----
    meeting_id = str(uuid.uuid4())
    store_meeting(meeting_id=meeting_id, title=title, notes=notes)

    return {
        "meeting_id": meeting_id,
        "title": title,
        "summary": summary,
        "action_items": action_items,
        "follow_ups": follow_ups,
        "next_steps": next_steps,
        "notes_length": len(notes),
    }


@app.post("/search")
def search(req: SearchRequest):
    """RAG-based Q&A across all stored meetings."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty")
    try:
        answer = search_qa_chain.invoke({"question": req.question})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
    return {"question": req.question, "answer": answer}


@app.get("/meetings")
def get_all_meetings():
    """List every stored meeting (id, title, date)."""
    return {"meetings": list_meetings()}


@app.post("/export")
def export_meeting(req: ExportRequest):
    """
    Save the processed meeting outputs as a .txt file and return
    the download path.
    """
    safe_title = "".join(c for c in req.title if c.isalnum() or c in " -_").strip()
    filename = f"{safe_title or 'meeting'}_{req.meeting_id[:8]}.txt"
    path = os.path.join(EXPORT_DIR, filename)

    content = (
        f"Meeting: {req.title}\n"
        f"Meeting ID: {req.meeting_id}\n"
        f"Exported at: {datetime.utcnow().isoformat()} UTC\n"
        f"{'=' * 60}\n\n"
        f"SUMMARY\n{'-' * 60}\n{req.summary}\n\n"
        f"ACTION ITEMS\n{'-' * 60}\n{req.action_items}\n\n"
        f"FOLLOW-UP QUESTIONS\n{'-' * 60}\n{req.follow_ups}\n\n"
        f"NEXT STEPS\n{'-' * 60}\n{req.next_steps}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return FileResponse(path, filename=filename, media_type="text/plain")


# ---------------- Serve frontend ----------------
if os.path.isdir("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/")
    def root():
        return FileResponse("frontend/index.html")
