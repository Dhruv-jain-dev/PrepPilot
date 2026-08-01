"""Server-side helpers for the ElevenLabs speech APIs."""

from __future__ import annotations

import os
from importlib import import_module
from io import BytesIO


class ElevenLabsAudioError(RuntimeError):
    """A safe error message for an ElevenLabs audio request."""


def _client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ElevenLabsAudioError("Voice features need ELEVENLABS_API_KEY in your .env file.")
    try:
        client_module = import_module("elevenlabs.client")
        eleven_labs_class = client_module.ElevenLabs
    except ImportError as exc:
        raise ElevenLabsAudioError("Install project dependencies to enable voice features.") from exc
    return eleven_labs_class(api_key=api_key)


def transcribe_audio(audio_bytes: bytes, file_name: str = "answer.wav") -> str:
    """Convert a recorded candidate answer to text with ElevenLabs Scribe."""
    if not audio_bytes:
        raise ElevenLabsAudioError("Record an answer before transcribing it.")
    audio_file = BytesIO(audio_bytes)
    audio_file.name = file_name
    try:
        transcript = _client().speech_to_text.convert(
            file=audio_file, model_id="scribe_v2", language_code="eng"
        )
    except Exception as exc:
        raise ElevenLabsAudioError("ElevenLabs could not transcribe that recording. Please try again.") from exc
    text = getattr(transcript, "text", "").strip()
    if not text:
        raise ElevenLabsAudioError("No speech was detected in that recording. Please try again.")
    return text


def synthesize_speech(text: str) -> bytes:
    """Generate a low-latency spoken interviewer response."""
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    try:
        audio = _client().text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_flash_v2_5",
            output_format="mp3_22050_32",
        )
        return b"".join(chunk for chunk in audio if chunk)
    except Exception as exc:
        raise ElevenLabsAudioError("ElevenLabs could not create interviewer audio. Please try again.") from exc
