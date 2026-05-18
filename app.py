import uuid
from pathlib import Path

import chromadb.errors
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, Field

from persona_engine import PersonaBot

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Persona chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, PersonaBot] = {}
_MAX_SESSIONS = 200


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


def _get_or_create_bot(session_id: str) -> PersonaBot:
    if session_id not in _sessions:
        if len(_sessions) >= _MAX_SESSIONS:
            # Drop oldest key (insertion order preserved in Py 3.7+)
            oldest = next(iter(_sessions))
            del _sessions[oldest]
        _sessions[session_id] = PersonaBot()
    return _sessions[session_id]


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message is empty.")

    sid = body.session_id.strip() if body.session_id else str(uuid.uuid4())
    if not sid:
        sid = str(uuid.uuid4())

    try:
        bot = _get_or_create_bot(sid)
        reply = bot.ask(text)
    except OpenAIError as exc:
        err = str(exc).lower()
        if "api_key" in err or "credentials" in err or "missing" in err:
            detail = (
                "OpenAI API key is missing for this server process. "
                "Export OPENAI_API_KEY in the same terminal where you run uvicorn, then restart."
            )
        else:
            detail = f"OpenAI error: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except chromadb.errors.NotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Chroma collection 'persona' not found. Run `python ingest.py` in this project, then try again.",
        ) from exc

    return ChatResponse(reply=reply, session_id=sid)


@app.get("/")
def index() -> FileResponse:
    path = STATIC_DIR / "index.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="UI not found.")
    return FileResponse(path)


app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)
