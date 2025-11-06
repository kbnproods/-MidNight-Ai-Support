from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from groq import Groq

from .assistant import AssistantConfig, build_messages, load_persona

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_ROOT = BASE_DIR / "web"
ASSETS_DIR = WEB_ROOT / "assets"

if not WEB_ROOT.exists():
    raise RuntimeError(
        "Web assets directory is missing. Expected to find 'web/' alongside src/."
    )


class ConversationMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ConversationMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str


def _load_runtime() -> tuple[AssistantConfig, Groq]:
    config = AssistantConfig.load()
    client = Groq(api_key=config.api_key)
    return config, client


CONFIG, CLIENT = _load_runtime()

app = FastAPI(title="MidNight AI", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"]
)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


def _call_groq(messages: List[dict[str, str]]) -> str:
    request_kwargs = {"model": CONFIG.model, "messages": messages}
    if CONFIG.max_tokens is not None:
        request_kwargs["max_tokens"] = CONFIG.max_tokens

    completion = CLIENT.chat.completions.create(**request_kwargs)
    return completion.choices[0].message.content


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    history_pairs = [(message.role, message.content) for message in request.history]
    history_pairs.append(("user", request.message))

    try:
        persona_text = load_persona(CONFIG.persona_path)
    except FileNotFoundError as exc:
        LOGGER.error("Persona file missing: %s", exc)
        raise HTTPException(status_code=500, detail="Persona file not found") from exc

    messages = build_messages(persona_text, history_pairs)

    try:
        reply = await run_in_threadpool(_call_groq, messages)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Groq API call failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(reply=reply)


@app.get("/api/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=False)
