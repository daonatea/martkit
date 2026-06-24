"""Transcripción de audio local con faster-whisper.

Corre 100% offline tras descargar el modelo una vez; multilingüe; no requiere
ffmpeg del sistema (trae las libs de FFmpeg vía PyAV). El modelo se descarga a
MODEL_DIR en el primer uso y queda cacheado allí.
"""
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}

_MODEL_SIZE = "base"
# Carpeta propia de descarga para poder detectar de forma fiable si el modelo
# ya está en caché (en Windows y macOS).
MODEL_DIR = Path.home() / ".markit" / "whisper-models"

_model = None


def is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def is_model_cached() -> bool:
    """True si el modelo Whisper ya fue descargado a MODEL_DIR."""
    return MODEL_DIR.exists() and any(MODEL_DIR.rglob("model.bin"))


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _model = WhisperModel(
            _MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root=str(MODEL_DIR),
        )
    return _model


def transcribe_audio(path: str) -> str:
    """Devuelve el texto transcrito (cuerpo), o '' si no hay habla."""
    model = _get_model()
    segments, _info = model.transcribe(path)
    return "\n\n".join(seg.text.strip() for seg in segments if seg.text.strip())
