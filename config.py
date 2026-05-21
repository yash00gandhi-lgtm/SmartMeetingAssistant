"""
config.py
---------
All settings live here. Values come from the .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- LLM provider ----------
# "openrouter" (default) or "groq"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# OpenRouter — get a free key from https://openrouter.ai
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Groq — alternative provider, key from https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ---------- Embeddings ----------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ---------- Storage ----------
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
EXPORT_DIR = os.getenv("EXPORT_DIR", "./exports")

os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

if LLM_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    print("⚠️  WARNING: OPENROUTER_API_KEY is empty.")
elif LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    print("⚠️  WARNING: GROQ_API_KEY is empty.")
