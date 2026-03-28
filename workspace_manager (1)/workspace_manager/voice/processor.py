"""
voice/processor.py

Offline speech-to-text via Vosk or Whisper-tiny.
Falls back gracefully when audio libs are absent.
"""

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── Optional imports ──────────────────────────────────────────────────────────

try:
    import sounddevice as sd
    import numpy as np
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


# ── VoskProcessor ─────────────────────────────────────────────────────────────

class VoskProcessor:
    """Real-time Vosk STT using a streaming callback."""

    SAMPLE_RATE = 16000
    BLOCK_SIZE = 8000

    def __init__(self, model_path: str, on_result: Callable[[str], None]):
        self._on_result = on_result
        self._running = False
        self._model = None
        self._model_path = model_path

    def _load_model(self) -> bool:
        if not VOSK_AVAILABLE:
            logger.error("vosk not installed.")
            return False
        path = Path(self._model_path)
        if not path.exists():
            logger.error("Vosk model not found at %s", path)
            return False
        try:
            vosk.SetLogLevel(-1)
            self._model = vosk.Model(str(path))
            return True
        except Exception as e:
            logger.error("Failed to load Vosk model: %s", e)
            return False

    def listen_once(self) -> Optional[str]:
        """Record ~3 seconds and return transcript."""
        if not SD_AVAILABLE:
            return None
        if not self._load_model():
            return None

        import json
        rec = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE)
        duration = 3  # seconds
        frames = sd.rec(
            int(duration * self.SAMPLE_RATE),
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        rec.AcceptWaveform(frames.tobytes())
        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip() or None


# ── WhisperProcessor ──────────────────────────────────────────────────────────

class WhisperProcessor:
    """Whisper-tiny offline STT."""

    SAMPLE_RATE = 16000

    def __init__(self, model_size: str, on_result: Callable[[str], None]):
        self._on_result = on_result
        self._model_size = model_size
        self._model = None

    def _load_model(self) -> bool:
        if not WHISPER_AVAILABLE:
            logger.error("openai-whisper not installed.")
            return False
        try:
            self._model = whisper.load_model(self._model_size)
            return True
        except Exception as e:
            logger.error("Failed to load Whisper model: %s", e)
            return False

    def listen_once(self) -> Optional[str]:
        if not SD_AVAILABLE:
            return None
        if not self._load_model():
            return None

        import tempfile, scipy.io.wavfile as wav, numpy as np

        duration = 4
        audio = sd.rec(
            int(duration * self.SAMPLE_RATE),
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        wav.write(tmp, self.SAMPLE_RATE, audio)

        result = self._model.transcribe(tmp, language="en", fp16=False)
        return result.get("text", "").strip() or None


# ── Public VoiceProcessor facade ──────────────────────────────────────────────

class VoiceProcessor:
    """
    High-level voice processor. Picks Vosk or Whisper based on config.
    Exposes `listen_once()` — runs in a background thread so the UI stays responsive.
    """

    def __init__(self, backend: str = "vosk", model_path: str = "", whisper_model: str = "tiny"):
        self._backend = backend
        self._model_path = model_path
        self._whisper_model = whisper_model

    @property
    def is_available(self) -> bool:
        if not SD_AVAILABLE:
            return False
        if self._backend == "vosk":
            return VOSK_AVAILABLE and Path(self._model_path).exists()
        if self._backend == "whisper":
            return WHISPER_AVAILABLE
        return False

    def listen_async(self, callback: Callable[[Optional[str]], None]) -> None:
        """
        Spawn a thread that records and calls callback(text) when done.
        callback receives None on failure.
        """
        def _worker():
            try:
                text = self._listen()
            except Exception as e:
                logger.error("Voice listen error: %s", e)
                text = None
            callback(text)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _listen(self) -> Optional[str]:
        dummy_cb = lambda x: None
        if self._backend == "vosk":
            proc = VoskProcessor(self._model_path, dummy_cb)
        else:
            proc = WhisperProcessor(self._whisper_model, dummy_cb)
        return proc.listen_once()
