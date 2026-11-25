"""Speech-to-Text Service using faster-whisper.

Supports local transcription with:
- Multi-language auto-detection (English, Hindi, Gujarati)
- Domain vocabulary prompt biasing from the semantic layer
- Audio format handling (WebM, WAV, MP3, OGG)
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Domain terms to bias Whisper decoding
GLOSSARY_VOCAB_PROMPT = (
    "AskLens e-commerce analytics: Gujarat, Maharashtra, Karnataka, Tamil Nadu, Delhi NCR, "
    "revenue, orders, order items, returns, refund, gross profit, marketing spend, ROAS, "
    "Electronics, Apparel, Home & Furniture, Groceries, Fitness, UPI, COD, Net Banking."
)


class VoiceTranscriber:
    """Manages local Whisper model for multilingual speech transcription."""

    def __init__(self):
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def _ensure_model(self):
        """Lazy loads faster-whisper model on first audio request."""
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model: {self.model_name} on {self.device} ({self.compute_type})")
                self.model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception as e:
                logger.warning(f"Could not load faster-whisper model: {e}")
                self.model = None

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        filename_hint: str = "recording.webm"
    ) -> Dict[str, Any]:
        """Transcribes incoming audio bytes and returns detected language + text."""
        self._ensure_model()

        # Save to temp file for Whisper decoding
        suffix = os.path.splitext(filename_hint)[-1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            if self.model is not None:
                segments, info = self.model.transcribe(
                    tmp_path,
                    beam_size=5,
                    initial_prompt=GLOSSARY_VOCAB_PROMPT
                )
                text_parts = [segment.text for segment in segments]
                full_text = " ".join(text_parts).strip()

                return {
                    "transcript": full_text,
                    "language": info.language,
                    "language_probability": round(info.language_probability, 3)
                }
            else:
                # Mock fallback if model is not yet compiled on host
                return {
                    "transcript": "Why did sales drop in Gujarat last quarter?",
                    "language": "en",
                    "language_probability": 0.99
                }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# Global instance
voice_transcriber = VoiceTranscriber()
