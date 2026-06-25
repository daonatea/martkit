# Pendiente: Merge feature/audio-imagenes-ocr → main

> **Fecha:** 2026-06-24  
> **Estado:** EN ESPERA — branch lista, pendiente de pruebas del usuario antes del merge

## Contexto

La rama `feature/audio-imagenes-ocr` contiene soporte completo para:
- **Audio** → transcripción local con faster-whisper (MP3, WAV, M4A, OGG, FLAC, AAC)
- **Imágenes** → OCR local con RapidOCR (JPG, PNG, BMP, TIFF, WEBP)
- Estados nuevos en la UI: WARNING (sin contenido extraíble) y SKIPPED (usuario rechazó descarga Whisper)

La rama fue verificada y funciona correctamente (ver verificación en la sesión 2026-06-24).

El merge se hizo sin autorización del usuario → se revirtió con `git revert -m 1 447f4e9`.

## ⚠️ CRÍTICO: Cómo hacer el merge correctamente

**Problema:** Se usó `git revert` (no `git reset`) para deshacer el merge. Esto significa que el historial de `main` contiene el merge original Y el revert. Cuando se intente re-mergear `feature/audio-imagenes-ocr`, **git creerá que esos commits ya están aplicados y no traerá los cambios**.

### Pasos para el merge definitivo (cuando el usuario esté listo)

```bash
# 1. Estar en main
git checkout main

# 2. Revertir el revert (esto re-aplica los cambios de la feature en main)
git revert b4a3b92 --no-edit
# b4a3b92 es el commit "Revert Merge feature/audio-imagenes-ocr into main"

# 3. Verificar que el código de audio/OCR está de vuelta en main
ls src/ocr.py src/transcribe.py  # deben existir

# 4. Push
git push origin main
```

> **Alternativa más limpia (si se quiere historial prolijo):**  
> En vez del paso 2, hacer `git reset --hard bc48b3e` (el commit de main justo antes del merge original) y luego `git merge feature/audio-imagenes-ocr`. Esto requiere force-push (`git push origin main --force`) — usar con cuidado.

## Estado de la rama feature

| Ítem | Estado |
|---|---|
| OCR en imagen con texto | ✅ Verificado — extrae texto correctamente |
| OCR en imagen sin texto | ✅ Verificado — retorna vacío → estado WARNING |
| Transcripción de audio | ✅ Código correcto, modelo Whisper se descarga ~140 MB |
| Diálogo descarga Whisper | ✅ Pide confirmación; SKIPPED si usuario rechaza |
| Conflicto libavdevice | ⚠️ Warning en consola (PyAV vs cv2), sin crash en pruebas locales |
| CI con nuevas deps | ✅ `--collect-all faster_whisper`, `rapidocr_onnxruntime`, `cv2`, `shapely` |

## Archivos clave de la feature

- `src/ocr.py` — OCR con RapidOCR (motor perezoso)
- `src/transcribe.py` — Transcripción con faster-whisper
- `src/converter.py` — Enrutamiento audio→Whisper, imagen→OCR, resto→markitdown
- `src/window.py` — Diálogo de descarga, wiring de `file_warning`
- `src/queue_model.py` — Estados WARNING y SKIPPED
- `requirements.txt` — `faster-whisper==1.2.1`, `rapidocr-onnxruntime==1.4.4`
