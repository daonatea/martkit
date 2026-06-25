# Plan de implementación — Audio (Whisper), Imágenes (OCR) y manejo de "sin contenido"

> Documento de planeación para markIT. Captura las decisiones acordadas, los
> hallazgos técnicos sobre las librerías y el plan de implementación por fases.
> Pensado para que un agente (p. ej. superpowers) lo analice y/o lo ejecute.
>
> Estado: **APROBADO el enfoque; pendiente de ejecutar.**
> Fecha: 2026-06-24

---

## 0. Contexto del proyecto

markIT es una app de escritorio (PyQt6, macOS + Windows) que convierte documentos
a Markdown. **No convierte por sí misma**: delega en la librería `markitdown` de
Microsoft (`MarkItDown().convert(path)` en `src/converter.py`).

### Estado actual ya implementado (antes de este plan)
- **Audio con faster-whisper local** ya integrado: `src/transcribe.py`, enrutamiento
  en `src/converter.py`, extensiones en `src/drop_zone.py`, íconos en `src/queue_model.py`.
- **YouTube eliminado** (era frágil por bloqueos de IP / PoToken de YouTube).
- **Bug del log arreglado**: `/tmp/markit.log` → `tempfile.gettempdir()` (servía en Mac, no en Windows).
- `requirements.txt`: agregado `faster-whisper==1.2.1`; quitados `pydub`,
  `SpeechRecognition`, `youtube-transcript-api`.
- Build scripts y CI (`build.sh`, `build-windows.bat`, `.github/workflows/build.yml`)
  actualizados para recolectar `faster_whisper`, `ctranslate2`, `av` y soltar los paquetes removidos.

### Lo que falta (este plan)
1. OCR de imágenes (JPG/PNG/…).
2. Diálogo de descarga del modelo de audio + estado "Omitido".
3. Manejo de archivos sin contenido (warning, no generar `.md`).
4. Confirmar/ajustar cobertura de formatos de oficina.

---

## 1. Decisiones acordadas con el usuario

| # | Tema | Decisión |
|---|------|----------|
| 1 | Modelo de audio | **faster-whisper local** (offline, multilingüe). NO se pre-empaqueta el modelo. |
| 2 | Descarga del modelo de audio | Se descarga en el primer uso (~140 MB). Al **agregar** un audio, mostrar diálogo pidiendo aceptar la descarga, **solo si el modelo no está en caché**. |
| 3 | Si el usuario rechaza la descarga | El audio **se agrega a la cola pero queda como "Omitido"** (no se convierte). |
| 4 | YouTube | **Fuera** (quitado del README y dependencias). |
| 5 | Imágenes | Soportar con **OCR local**. Librería: **`rapidocr-onnxruntime==1.4.4`** (modelos empaquetados, sin descarga, offline). Formatos: `jpg, jpeg, png, bmp, tiff, tif, webp`. |
| 6 | Formatos legacy `.doc` / `.ppt` | **Quitar del selector** (markitdown NO los convierte: `mammoth` solo `.docx`, `python-pptx` solo `.pptx`). |
| 7 | Excel | **Sí funciona**: `.xlsx` (openpyxl/pandas) y `.xls` (xlrd, ya instalado). Ambos se mantienen. |
| 8 | `.txt` / `.md` | **Agregar al selector** (markitdown los soporta; faltaban). |
| 9 | Archivo sin contenido (imagen sin texto, audio sin habla, doc vacío) | **NO generar `.md`.** Mostrar en la fila un **warning (no error)**: *"El archivo no contenía nada para convertir."* (inline, sin popup). |

---

## 2. Hallazgos técnicos sobre librerías (verificados)

### markitdown 0.1.6 — qué convierte realmente
- ✅ **Funcionan**: docx, xlsx, xls, pptx, txt, md, csv, json, xml, html, pdf, epub, msg, zip, ipynb.
- ❌ **NO funcionan**: `.doc` y `.ppt` (formatos binarios viejos) — no tienen convertidor.
- ❌ **Imágenes**: por defecto solo extrae metadatos EXIF, o una *descripción* si se le conecta un LLM. **No hace OCR de texto.** Por eso el OCR lo hacemos aparte.
- Fuentes: <https://github.com/microsoft/markitdown>,
  <https://github.com/microsoft/markitdown/blob/main/packages/markitdown-ocr/README.md>

### Audio — faster-whisper
- Corre **100% offline** tras descargar el modelo una vez; **no requiere ffmpeg del sistema** (trae las libs vía PyAV); multilingüe; ~4× más rápido que openai-whisper.
- Versión: **1.2.1**.
- Fuente: <https://github.com/SYSTRAN/faster-whisper>

### OCR — elección de librería
Para offline, sin binarios del sistema y empaquetable con PyInstaller, **RapidOCR es la mejor opción**:

| Librería | Veredicto |
|---|---|
| **RapidOCR (onnxruntime)** | ✅ Liviana, offline, usa `onnxruntime` (ya viene con `magika`), sin binarios del sistema |
| Tesseract / pytesseract | ❌ Requiere instalar el binario Tesseract en cada PC |
| EasyOCR | ❌ Arrastra PyTorch (~2 GB) |
| PaddleOCR | ❌ Arrastra PaddlePaddle, pesado y difícil de empaquetar |

- **Paquete elegido: `rapidocr-onnxruntime==1.4.4`** porque **empaqueta los modelos ONNX en el paquete** → funciona offline sin descargar nada.
  (El paquete nuevo `rapidocr` 3.9.0 descarga modelos bajo demanda desde un CDN → no sirve para offline inmediato.)
- Formatos de entrada (vía OpenCV/PIL): jpg, jpeg, png, bmp, tiff/tif, webp.
- Idiomas: inglés/latino por defecto. **Aviso**: tildes y ñ pueden fallar con el modelo base; usar el mejor modelo latino/multilingüe disponible.
- Fuentes: <https://pypi.org/project/rapidocr-onnxruntime/>,
  <https://pypi.org/project/rapidocr/>, <https://github.com/RapidAI/RapidOCR>

---

## 3. Plan de implementación por fases

### Fase 0 — Dependencias
- `requirements.txt`: agregar `rapidocr-onnxruntime==1.4.4`. Deps transitivas
  (`opencv-python`, `shapely`, `pyclipper`, `Pillow`, `numpy`, `onnxruntime`) las resuelve pip.

### Fase 1 — Estados nuevos (`src/queue_model.py`)
- `FileStatus`: agregar `WARNING = "warning"` y `SKIPPED = "skipped"`.
- `type_icon`: imágenes (`jpg/jpeg/png/bmp/tiff/tif/webp` → 🖼️), `txt/md` → 📄 (audio ya está).

### Fase 2 — Módulo de audio (`src/transcribe.py`, ya existe)
- Definir `MODEL_DIR` (carpeta de datos de la app) y usarla como `download_root`.
- Nueva función `is_model_cached()` → comprueba si el modelo ya está descargado.
- `transcribe_audio()` devuelve **solo el texto transcrito** (puede ser `""`); el header lo arma el converter.

### Fase 3 — Módulo nuevo de OCR (`src/ocr.py`)
- `IMAGE_EXTS = {.jpg, .jpeg, .png, .bmp, .tiff, .tif, .webp}`, `is_image(path)`.
- Init perezoso del motor RapidOCR (mejor modelo latino disponible).
- `ocr_image(path)` → texto extraído unido, o `""` si no hay nada.

### Fase 4 — Enrutamiento y warning (`src/converter.py`)
- Nueva señal `file_warning = pyqtSignal(str, str)`.
- Enrutar: `audio → transcribe` · `imagen → ocr` · `resto → markitdown` (carga perezosa de markitdown).
- **Regla de vacío unificada**: si el texto extraído (sin espacios) está vacío →
  emitir `file_warning` y **NO escribir `.md`**. Si hay contenido → escribir y `file_finished`.
- Audio/imagen: anteponer título `# {nombre}`; documentos: Markdown de markitdown tal cual.

### Fase 5 — Textos (`src/i18n.py`) ES + EN
- `status_warning`, `status_skipped`.
- `warn_no_content` = "El archivo no contenía nada para convertir."
- Diálogo de audio: título, cuerpo (~140 MB, una sola vez), botones "Descargar y continuar" / "Omitir audio".

### Fase 6 — Pintado de la cola (`src/queue_widget.py`)
- `FileRow.refresh()`:
  - `WARNING` → ámbar `⚠`, fondo suave, **tooltip** con el mensaje (sin popup).
  - `SKIPPED` → gris "Omitido".
- Agregar colores `_CLR_WARN / _BG_WARN / _CLR_SKIP`.

### Fase 7 — Zona de carga (`src/drop_zone.py`)
- `_SUPPORTED_EXTS`: **quitar** `.doc` y `.ppt`; **agregar** `.txt`, `.md` y las 7 de imagen
  (audio ya está). El filtro del diálogo y la validación de arrastre se derivan de esa tupla.

### Fase 8 — Ventana / lógica de audio (`src/window.py`)
- Conectar `worker.file_warning` → `queue.update_status(path, WARNING, msg)` (inline, sin modal).
- En `_on_files_added`: detectar audios. Si hay audio **y** `not is_model_cached()` →
  `QMessageBox` de pregunta:
  - **Descargar y continuar** → se agregan normal (descarga en la 1ª conversión).
  - **Omitir audio** → los no-audio entran normal; cada audio entra y queda `SKIPPED`.
- `waiting_paths()` ya excluye `SKIPPED`, así que el worker no los procesa.

### Fase 9 — Empaquetado (`build.sh`, `build-windows.bat`, `.github/workflows/build.yml` ×3)
- Agregar `--hidden-import ocr`, `--collect-all rapidocr_onnxruntime` (incluye modelos ONNX),
  `--collect-all shapely` (libs nativas) y `--collect-all cv2`.
- ⚠️ Validar con un **build real** (RapidOCR/shapely/opencv tienen binarios nativos).

### Fase 10 — README
- Tabla de formatos: agregar fila **Images** (JPG, JPEG, PNG, BMP, TIFF, WEBP — texto vía OCR local offline).
- Nota: archivos sin texto/habla no generan `.md`, muestran una advertencia.

### Fase 11 — Pruebas (`tests/`)
- `conftest.py`: fixture `tmp_png` (PNG mínimo válido).
- `test_converter.py`:
  - imagen → OCR (stub `converter.ocr_image`) genera `.md` con el texto.
  - resultado vacío → emite `file_warning` y **no** crea archivo.
- Las pruebas stubean OCR/Whisper para no requerir modelos.

### Fase 12 — Verificación
- `py_compile` de todo (sintaxis) — se puede aquí.
- ⚠️ `pytest` y build **no** corren en la máquina actual (sin `.venv` con deps).
  Quedan para el entorno del usuario / CI: `pip install -r requirements.txt && pytest`.

---

## 4. Enrutamiento final (resumen)

```
audio (mp3/wav/m4a/ogg/flac/aac)  → Whisper local   (diálogo descarga 1ª vez; si rechaza → "Omitido")
imagen (jpg/jpeg/png/bmp/tiff/webp) → RapidOCR local (modelos ya empaquetados, sin descarga)
resto                              → markitdown
→ si el texto extraído queda vacío → NO generar .md → warning "El archivo no contenía nada para convertir."
```

---

## 5. Riesgos / cosas a vigilar
1. **Empaquetado de RapidOCR + shapely + opencv** con PyInstaller (binarios nativos) — el punto más frágil; se confirma con un build real en CI.
2. **Acentos / ñ en OCR** — el modelo base latino puede equivocarse en tildes.
3. **Detección de modelo Whisper en caché** — fijar `download_root` propio para que `is_model_cached()` sea fiable en Windows y Mac.

## 6. Archivos a tocar
`requirements.txt`, `src/queue_model.py`, `src/transcribe.py`, **`src/ocr.py` (nuevo)**,
`src/converter.py`, `src/i18n.py`, `src/queue_widget.py`, `src/drop_zone.py`, `src/window.py`,
`build.sh`, `build-windows.bat`, `.github/workflows/build.yml`, `README.md`,
`tests/conftest.py`, `tests/test_converter.py`.
