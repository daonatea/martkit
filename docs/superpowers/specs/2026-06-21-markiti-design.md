# Markiti — Spec de diseño
**Fecha:** 2026-06-21

## Resumen

App Mac de escritorio que envuelve la librería [markitdown](https://github.com/microsoft/markitdown) de Microsoft para convertir documentos (PDF, Word, Excel, PowerPoint, HTML, CSV, etc.) a formato Markdown. Dirigida a usuarios no técnicos — en particular una usuaria que no tiene contexto de línea de comandos.

---

## Propósito y contexto

markitdown es una librería Python que convierte múltiples formatos de archivo a Markdown optimizado para LLMs. La herramienta existe pero no tiene interfaz gráfica. Esta app resuelve eso: una ventana Mac limpia donde se arrastran archivos y salen convertidos, sin terminal, sin configuración técnica.

---

## Usuario objetivo

- Usuaria no técnica en Mac
- Uso personal en un solo equipo
- No requiere firma de desarrollador Apple (distribución por copia directa del `.app`)
- Primera apertura: clic derecho → Abrir (bypass Gatekeeper, solo primera vez)

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Lógica de conversión | `markitdown[all]` (Python) |
| UI | PyQt6 |
| Empaquetado | PyInstaller → `.app` nativo Mac |
| Localización | Detección automática del idioma del sistema (`QLocale`) — español si Mac en español, inglés si no |

---

## Diseño de la ventana

**Tamaño:** 640 × 460 px, no redimensionable (o con mínimo fijo).

### Barra superior — carpeta de salida

```
📁 Salida: ~/Documents/Markdown convertidos    [Cambiar…]
```

- Configurable con diálogo nativo de carpeta (`QFileDialog`)
- Se persiste entre sesiones (`QSettings`)
- Por defecto: `~/Documents/Markiti`

### Cuerpo principal — dos paneles

**Panel izquierdo (48% del ancho) — Drop zone**

- Fondo ligeramente distinto (`#fafafa`) con blob animado pulsante centrado
- Zona de arrastre con borde dashed que cambia a azul al pasar archivos encima
- Icono de carpeta grande (🗂️) + texto "Arrastra tus archivos aquí"
- Subtexto: "O selecciónalos con el botón"
- Tags de formatos soportados: PDF · Word · Excel · PowerPoint · HTML · +más
- Botón "Seleccionar archivos…" — abre `QFileDialog` con filtros de formatos soportados, selección múltiple habilitada

**Panel derecho (resto del ancho) — Cola de archivos**

Header: `ARCHIVOS` · `N en cola` · botón `Limpiar`

Lista scrolleable de ítems, cada uno con:
- Icono según tipo de archivo (emoji por extensión)
- Nombre del archivo (truncado con `…` si es largo)
- Tamaño del archivo
- Estado:
  - `— En espera` (gris) — archivo añadido, conversión no iniciada
  - `⏳ Convirtiendo` (azul) + barra de progreso animada en la parte inferior del ítem
  - `✓ Listo` (verde) — conversión exitosa
  - `✗ Error` (rojo) — conversión fallida (tooltip con mensaje de error)

### Barra inferior — acciones

```
[1 / 4 listos]  |  [Convertir todo →]  [🗂️ Abrir carpeta]
```

- **Contador:** `N / M listos` (actualizado en tiempo real)
- **Convertir todo:** dispara conversión secuencial de todos los archivos en espera; el botón cambia a "Cancelar" mientras se ejecuta
- **Abrir carpeta:** abre la carpeta de salida en Finder (`QDesktopServices.openUrl`)

---

## Comportamiento de conversión

1. El usuario añade archivos (drag & drop o selector) → aparecen en la cola como "En espera"
2. Al presionar "Convertir todo":
   - Los archivos se procesan uno a uno (hilo secundario, no bloquea UI)
   - Cada ítem actualiza su estado en tiempo real
   - El archivo de salida se guarda en la carpeta de salida configurada, con el mismo nombre base + `.md`
   - Si ya existe un `.md` con ese nombre, se sobreescribe sin preguntar
3. La app permanece abierta al terminar — el usuario puede añadir más archivos
4. El botón "Limpiar" borra la lista (no elimina los archivos `.md` ya generados)

### Threading

- La conversión corre en `QThread` para no bloquear el hilo principal
- Señales Qt (`pyqtSignal`) comunican el progreso al hilo de UI: `started`, `progress`, `finished`, `error`

---

## Localización

Strings en dos archivos `.ts` (Qt Linguist):

| Clave | Español | English |
|---|---|---|
| `drop_hint` | Arrastra tus archivos aquí | Drop your files here |
| `btn_select` | Seleccionar archivos… | Select files… |
| `btn_convert` | Convertir todo → | Convert all → |
| `btn_cancel` | Cancelar | Cancel |
| `btn_open_folder` | Abrir carpeta | Open folder |
| `status_waiting` | En espera | Waiting |
| `status_converting` | Convirtiendo | Converting |
| `status_done` | Listo | Done |
| `status_error` | Error | Error |
| `folder_label` | Salida: | Output: |
| `folder_change` | Cambiar… | Change… |
| `queue_clear` | Limpiar | Clear |
| `queue_header` | Archivos | Files |
| `counter` | {done} / {total} listos | {done} / {total} done |

La app detecta `QLocale.system().language()` al arrancar y carga el archivo `.ts` correspondiente. Si el idioma no tiene traducción, usa inglés como fallback.

---

## Empaquetado (.app)

- PyInstaller con `--windowed` (sin terminal), `--onedir` (más rápido que `--onefile` en Mac)
- El resultado es `dist/Markiti.app` — se puede copiar a `/Applications` o distribuir por AirDrop
- Script `build.sh` con todos los flags necesarios

### Requisitos de dependencias

```
markitdown[all]
PyQt6
PyInstaller
```

---

## Formatos soportados (vía markitdown)

PDF · DOCX · XLSX · XLS · PPTX · HTML · CSV · JSON · XML · EPUB · MSG (Outlook) · ZIP (extrae e itera) · URLs de YouTube · Imágenes (EXIF + OCR con LLM opcional)

---

## Fuera de scope

- Firma de desarrollador Apple / notarización
- Distribución en Mac App Store
- Soporte Windows/Linux
- Vista previa del Markdown generado dentro de la app
- Configuración de opciones de markitdown (OCR, LLM, etc.)
- Actualización automática de la app
