"""
speech_to_text.py
------------------
Purpose: Server-side audio transcription using Whisper (via faster-whisper).

IMPORTANT: This module is OPTIONAL.
The frontend uses the browser's Web Speech API as the PRIMARY voice input method,
which works with zero server-side models. This module is only used as a fallback
when the browser sends a raw audio file to the /ivr/audio endpoint.

Fixes applied:
  - Model loads lazily in background (non-blocking)
  - WAV conversion from WebM/OGG/MP3 using pydub BEFORE passing to Whisper
  - All transcription runs in a thread pool via asyncio (never blocks event loop)
  - Full error handling with clear messages
  - Graceful degradation if faster-whisper or ffmpeg not installed
"""

import os
import logging
import asyncio
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="whisper")

# Check if pydub is available (for WebM → WAV conversion)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not installed. Audio conversion disabled. Run: pip install pydub")

# Check if faster-whisper is available
try:
    from faster_whisper import WhisperModel as _WhisperModelClass
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning(
        "faster-whisper not installed. Server-side STT disabled. "
        "Run: pip install faster-whisper  (optional — frontend uses Web Speech API)"
    )


def _load_model_sync():
    """Load Whisper model synchronously. Thread-safe, loads only once."""
    global _model
    if not FASTER_WHISPER_AVAILABLE:
        return None
    with _model_lock:
        if _model is not None:
            return _model
        try:
            logger.info(f"Loading Whisper model '{_model_size}'... (this may take 30-60s first time)")
            _model = _WhisperModelClass(
                _model_size,
                device="cpu",
                compute_type="int8",
            )
            logger.info(f"✅ Whisper model '{_model_size}' loaded.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            _model = None
    return _model


def _convert_to_wav(input_path: str) -> str:
    """
    Convert any audio format (WebM, OGG, MP3) to WAV using pydub.
    Returns path to the WAV file. Caller must delete it.
    
    Root cause fix: Whisper/ctranslate2 cannot natively decode WebM
    from the browser's MediaRecorder API. We must convert first.
    """
    if not PYDUB_AVAILABLE:
        logger.warning("pydub not available, returning original file path")
        return input_path

    ext = os.path.splitext(input_path)[1].lower()

    # Already WAV — no conversion needed
    if ext == ".wav":
        return input_path

    try:
        # Detect format from extension
        fmt_map = {
            ".webm": "webm",
            ".ogg":  "ogg",
            ".mp3":  "mp3",
            ".m4a":  "mp4",
            ".mp4":  "mp4",
            ".flac": "flac",
        }
        fmt = fmt_map.get(ext, "webm")  # Default assume webm (browser output)

        audio = AudioSegment.from_file(input_path, format=fmt)

        # Convert to 16kHz mono WAV (Whisper's expected format)
        audio = audio.set_frame_rate(16000).set_channels(1)

        wav_path = input_path.rsplit(".", 1)[0] + "_converted.wav"
        audio.export(wav_path, format="wav")
        logger.info(f"Audio converted: {ext} → WAV  ({len(audio)}ms)")
        return wav_path

    except Exception as e:
        logger.error(f"Audio conversion failed: {e}. Trying original file.")
        return input_path


def _transcribe_sync(file_path: str) -> str:
    """
    Synchronous transcription. Runs inside ThreadPoolExecutor.
    Converts to WAV first, then transcribes.
    """
    wav_path = None
    converted = False

    try:
        # Step 1: Convert to WAV if needed
        wav_path = _convert_to_wav(file_path)
        converted = (wav_path != file_path)

        # Step 2: Load model (cached after first load)
        model = _load_model_sync()
        if model is None:
            return ""

        # Step 3: Transcribe
        segments, info = model.transcribe(
            wav_path,
            beam_size=5,
            language="en",       # Force English for hospital IVR
            vad_filter=True,     # Filter silence/noise automatically
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text = " ".join(seg.text.strip() for seg in segments)
        logger.info(f"Transcribed: '{text}' (lang: {info.language}, prob: {info.language_probability:.2f})")
        return text.strip()

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""

    finally:
        # Clean up converted WAV file
        if converted and wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except Exception:
                pass


async def transcribe_audio(file_path: str) -> str:
    """
    Async entry point — transcribes audio WITHOUT blocking the FastAPI event loop.
    
    Root cause fix: The original code called transcription synchronously inside
    an async endpoint, blocking the entire server. Now runs in a thread pool.
    
    Args:
        file_path: Path to audio file (WebM, WAV, MP3, OGG)
    Returns:
        Transcribed text string, or empty string on failure.
    """
    if not FASTER_WHISPER_AVAILABLE:
        logger.warning("faster-whisper not available. Cannot transcribe server-side.")
        return ""

    loop = asyncio.get_event_loop()
    try:
        # Run blocking transcription in thread pool — never blocks event loop
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, _transcribe_sync, file_path),
            timeout=60.0  # 60 second max for transcription
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Transcription timed out after 60 seconds")
        return ""
    except Exception as e:
        logger.error(f"Transcription executor error: {e}")
        return ""
