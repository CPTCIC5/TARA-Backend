"""
voice_server.py — Drop-in voice layer for your existing Jarvis system.

New deps:  pip install fastapi uvicorn python-multipart httpx elevenlabs openai
Your existing deps (openai, sqlalchemy, dotenv) remain unchanged.

Run:  uvicorn voice_server:app --reload --port 3000
"""

import os, sys, io, json
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ── Import your existing Jarvis logic ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
# Adjust the import below to wherever your jarvis.py / llm.py lives
# e.g. from agents.jarvis import ask_llm, clear_conversation
from my_llm import ask_llm, clear_conversation          # ← change path if needed
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
VOICE_ID           = "UShdpPZj9t1Kgb9ACOS2"
EL_MODEL           = "eleven_turbo_v2_5"           # v2 (the fast expensive one)

app = FastAPI(title="Jarvis Voice API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── 1. Speech-to-Text via OpenAI Whisper ─────────────────────────────────────
async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    import openai
    client = openai.AsyncOpenAI()
    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = filename
    result = await client.audio.transcriptions.create(
        model="whisper-1",
        file=file_obj,
        response_format="text",
    )
    return result.strip()


# ── 2. ElevenLabs v2 STREAMING TTS ───────────────────────────────────────────
async def tts_stream(text: str) -> AsyncGenerator[bytes, None]:
    """
    Streams MP3 audio chunks from ElevenLabs as they arrive.
    Latency trick: ElevenLabs starts returning audio after ~200 ms
    because we use optimize_streaming_latency=4 (max) and chunk_length_schedule.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": EL_MODEL,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
        "optimize_streaming_latency": 4,   # 0-4, 4 = max latency optimisation
        "output_format": "mp3_44100_128",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as r:
            if r.status_code != 200:
                body = await r.aread()
                raise HTTPException(status_code=r.status_code,
                                    detail=f"ElevenLabs error: {body.decode()}")
            async for chunk in r.aiter_bytes(chunk_size=4096):
                if chunk:
                    yield chunk


# ── 3. Main voice endpoint ────────────────────────────────────────────────────
@app.post("/voice")
async def voice_endpoint(
    audio: UploadFile = File(...),
    user_id: int = Form(...),
):
    """
    Receives audio blob → transcribes → asks Jarvis → streams TTS back.
    The client can start playing audio before the full response is ready.
    """
    audio_bytes = await audio.read()

    # Step 1 – STT
    try:
        user_text = await transcribe(audio_bytes, audio.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

    if not user_text:
        raise HTTPException(status_code=400, detail="Could not understand audio")

    # Step 2 – LLM  (your existing synchronous function — run in thread pool)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, ask_llm, user_text, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM failed: {e}")

    # Step 3 – Stream TTS back with transcript in header so UI can show it
    # HTTP headers are latin-1 only — percent-encode to handle smart quotes,
    # em-dashes, and any other unicode the LLM may produce.
    from urllib.parse import quote
    safe_transcript = quote(user_text.replace("\n", " ")[:500], safe=" ,.'\"")
    safe_reply      = quote(reply.replace("\n",      " ")[:500], safe=" ,.'\"")

    return StreamingResponse(
        tts_stream(reply),
        media_type="audio/mpeg",
        headers={
            "X-User-Text":    safe_transcript,
            "X-Assistant-Text": safe_reply,
            "Access-Control-Expose-Headers": "X-User-Text, X-Assistant-Text",
        },
    )


# ── 4. Clear conversation ─────────────────────────────────────────────────────
@app.post("/clear")
async def clear_endpoint(user_id: int = Form(...)):
    clear_conversation(user_id)
    return {"status": "cleared"}


# ── 5. Serve the UI ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_path = Path(__file__).parent / "voice_ui.html"
    return HTMLResponse(html_path.read_text())