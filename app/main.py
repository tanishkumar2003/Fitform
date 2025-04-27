# File: app/main.py

import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db
from app.routers.journal import router as journal_router
from app.routers.sessions import router as session_router
from app.routers.advice import router as advice_router

# Configure the Gemini client
genai.configure(api_key=settings.gemini_api_key)

app = FastAPI(
    title="FitForm Journal API",
    version="0.1.0",
    debug=True,
)
#  ── ADD THIS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your Vite frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#  ─────────────────────────────────────────────────────────
# —— API routes —— #
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

@app.get("/debug/entries_count", tags=["debug"])
async def debug_entries_count():
    count = await db.entries.count_documents({})
    return {"entries_in_db": count}

app.include_router(journal_router)
app.include_router(session_router)
app.include_router(advice_router)

# —— Static files —— #
ROOT_DIR   = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(ROOT_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
