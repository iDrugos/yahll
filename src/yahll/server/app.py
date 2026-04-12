"""
Yahll web server — FastAPI backend with SSE streaming.
"""
import asyncio
import json
import os
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

# Whisper model — loaded once, reused across requests
_whisper = None
_whisper_lock = threading.Lock()

def _get_whisper():
    global _whisper
    if _whisper is None:
        with _whisper_lock:
            if _whisper is None:
                from faster_whisper import WhisperModel
                # Use GPU if available, fallback to CPU
                try:
                    _whisper = WhisperModel("base", device="cuda", compute_type="float16")
                except Exception:
                    _whisper = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper


UI_PATH = Path(__file__).parent / "ui.html"
OVERLAY_PATH = Path(__file__).parent / "overlay.html"


def create_app(agent, config: dict, jarvis_mode: bool = False) -> FastAPI:
    app = FastAPI(title="Yahll", docs_url=None, redoc_url=None)
    app.state.agent = agent
    app.state.config = config
    app.state.loop = None  # set at startup

    @app.on_event("startup")
    async def _store_loop():
        app.state.loop = asyncio.get_event_loop()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html_path = OVERLAY_PATH if jarvis_mode else UI_PATH
        return HTMLResponse(html_path.read_text(encoding="utf-8"))

    @app.get("/status")
    async def status():
        return {"model": config.get("model", "unknown"), "ok": True}

    class ChatRequest(BaseModel):
        message: str

    @app.post("/chat")
    async def chat(req: ChatRequest):
        q: asyncio.Queue = asyncio.Queue()
        loop = app.state.loop

        def on_token(text: str):
            asyncio.run_coroutine_threadsafe(
                q.put({"type": "token", "text": text}), loop
            )

        def on_tool(name: str, result):
            asyncio.run_coroutine_threadsafe(
                q.put({"type": "tool", "text": name}), loop
            )

        def run():
            try:
                msg = req.message
                if jarvis_mode:
                    msg = f"[Be brief. Max 2 sentences. No markdown. Plain text only.]\n\n{msg}"
                app.state.agent.stream_chat(msg, on_token=on_token, on_tool=on_tool)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    q.put({"type": "error", "text": str(e)}), loop
                )
            finally:
                asyncio.run_coroutine_threadsafe(q.put(None), loop)

        threading.Thread(target=run, daemon=True).start()

        async def generate():
            while True:
                item = await q.get()
                if item is None:
                    yield "data: [DONE]\n\n"
                    break
                yield f"data: {json.dumps(item)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.post("/clear")
    async def clear():
        app.state.agent.clear()
        return {"ok": True}

    @app.post("/skill")
    async def load_skill_endpoint(body: dict):
        from yahll.memory.knowledge_base import load_skill
        name = body.get("name", "")
        result = load_skill(name)
        if "error" in result:
            return JSONResponse(result, status_code=404)
        app.state.agent.inject_context(
            f"## SKILL: {result['name']}\n\n{result['content']}"
        )
        return {"loaded": result["name"]}

    @app.get("/skills")
    async def list_skills_endpoint():
        from yahll.memory.knowledge_base import list_skills
        return list_skills()

    @app.post("/transcribe")
    async def transcribe(audio: UploadFile = File(...)):
        """Receive audio blob, transcribe locally with Whisper, return text."""
        suffix = ".webm"
        try:
            # Save uploaded audio to a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await audio.read())
                tmp_path = tmp.name

            # Run Whisper in a thread (blocking)
            def run_whisper():
                model = _get_whisper()
                segments, _ = model.transcribe(tmp_path, language="en", beam_size=5)
                return " ".join(seg.text.strip() for seg in segments).strip()

            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, run_whisper)
            return {"text": text}

        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── Session history endpoints ──

    SESSIONS_DIR = os.path.expanduser("~/.yahll/sessions")

    @app.get("/sessions")
    async def list_sessions():
        """Return recent session patches sorted newest-first, max 20."""
        try:
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            files = sorted(
                [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")],
                reverse=True,
            )[:20]
            sessions = []
            for fname in files:
                fpath = os.path.join(SESSIONS_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "filename": fname,
                        "timestamp": data.get("timestamp", fname.replace(".json", "")),
                        "summary": data.get("summary", "no summary"),
                        "model": data.get("model", "unknown"),
                    })
                except Exception:
                    continue
            return sessions
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    class LoadSessionRequest(BaseModel):
        filename: str

    @app.post("/load-session")
    async def load_session(req: LoadSessionRequest):
        """Load a past session's context into the agent."""
        fpath = os.path.join(SESSIONS_DIR, req.filename)
        if not os.path.isfile(fpath):
            return JSONResponse({"error": "Session not found"}, status_code=404)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Build context from the session data
            parts = []
            if data.get("summary"):
                parts.append(f"Previous session: {data['summary']}")
            if data.get("learned"):
                parts.append("Known facts: " + ", ".join(data["learned"]))
            if data.get("next_context"):
                parts.append(f"Continue from: {data['next_context']}")
            context = "\n".join(parts) if parts else f"Session: {req.filename}"
            app.state.agent.inject_context(context)
            return {"ok": True, "summary": data.get("summary", "")}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    return app
