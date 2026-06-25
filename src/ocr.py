"""OCR local de imágenes con RapidOCR (rapidocr-onnxruntime).

Se usa porque markitdown no extrae texto de imágenes por sí solo (solo
metadatos o, con un LLM, una descripción). RapidOCR corre offline, trae los
modelos ONNX empaquetados y no requiere binarios del sistema.
"""
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# El motor es costoso de crear; se instancia una sola vez y se reutiliza.
_engine = None


def is_image(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def ocr_image(path: str) -> str:
    engine = _get_engine()
    result, _ = engine(path)
    if not result:
        return ""
    lines = [str(line[1]).strip() for line in result if len(line) > 1 and line[1]]
    return "\n".join(l for l in lines if l)
