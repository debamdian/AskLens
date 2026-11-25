"""Voice Audio Upload Router.

Receives audio recorded in the browser and returns transcribed text
with detected language for the user to confirm/edit before query execution.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.voice.transcriber import voice_transcriber

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Transcription"])


@router.post("/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Receives audio file from browser MediaRecorder and returns transcription."""
    if not file:
        raise HTTPException(status_code=400, detail="No audio file uploaded.")

    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio recording.")

    result = voice_transcriber.transcribe_audio_bytes(
        audio_bytes=audio_bytes,
        filename_hint=file.filename or "recording.webm"
    )

    return result
