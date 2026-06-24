"""Transcripción de audio local con faster-whisper.

Se usa en lugar del transcriptor nativo de markitdown, que depende de la API
gratuita de Google (requiere internet, casi solo inglés, falla con audios
largos) y de ffmpeg instalado en el sistema.

faster-whisper corre 100% offline, es multilingüe y trae las librerías de
FFmpeg empaquetadas vía PyAV, así que no exige ffmpeg en la máquina del usuario.
El modelo se descarga de Hugging Face en el primer uso y queda cacheado.
"""
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}

# Tamaño del modelo: "base" es buen equilibrio calidad/velocidad en CPU.
_MODEL_SIZE = "base"

# El modelo es costoso de cargar; se instancia una sola vez y se reutiliza.
_model = None


def is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(path: str) -> str:
    model = _get_model()
    segments, info = model.transcribe(path)
    body = "\n\n".join(
        seg.text.strip() for seg in segments if seg.text.strip()
    )
    title = Path(path).stem
    lang = getattr(info, "language", "?")
    header = f"# {title}\n\n_Transcripción automática · idioma detectado: {lang}_\n\n"
    return header + (body or "_(sin habla detectada)_") + "\n"
