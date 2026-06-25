from PyQt6.QtCore import QLocale

_STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "drop_hint": "Arrastra tus archivos aquí",
        "drop_sub": "O selecciónalos con el botón",
        "btn_select": "Seleccionar archivos…",
        "btn_convert": "Convertir todo →",
        "btn_cancel": "Cancelar",
        "btn_open_folder": "Abrir carpeta",
        "status_waiting": "En espera",
        "status_converting": "Convirtiendo",
        "status_done": "Listo",
        "status_error": "Error",
        "folder_label": "Salida:",
        "folder_change": "Cambiar…",
        "queue_clear": "Limpiar",
        "queue_header": "Archivos",
        "counter": "{done} / {total} listos",
        "status_warning": "Sin contenido",
        "status_skipped": "Omitido",
        "warn_no_content": "El archivo no contenía nada para convertir.",
        "audio_dl_title": "Descargar modelo de voz",
        "audio_dl_body": "Para convertir audio se debe descargar una sola vez un modelo de voz (~140 MB). ¿Deseas descargarlo ahora?",
        "audio_dl_accept": "Descargar y continuar",
        "audio_dl_skip": "Omitir audio",
        "window_title": "markIT",
    },
    "en": {
        "drop_hint": "Drop your files here",
        "drop_sub": "Or select them with the button",
        "btn_select": "Select files…",
        "btn_convert": "Convert all →",
        "btn_cancel": "Cancel",
        "btn_open_folder": "Open folder",
        "status_waiting": "Waiting",
        "status_converting": "Converting",
        "status_done": "Done",
        "status_error": "Error",
        "folder_label": "Output:",
        "folder_change": "Change…",
        "queue_clear": "Clear",
        "queue_header": "Files",
        "counter": "{done} / {total} done",
        "status_warning": "No content",
        "status_skipped": "Skipped",
        "warn_no_content": "The file had no content to convert.",
        "audio_dl_title": "Download speech model",
        "audio_dl_body": "Converting audio requires a one-time download of a speech model (~140 MB). Do you want to download it now?",
        "audio_dl_accept": "Download and continue",
        "audio_dl_skip": "Skip audio",
        "window_title": "markIT",
    },
}


def load_strings() -> dict[str, str]:
    lang = QLocale.system().name()[:2].lower()
    return _STRINGS.get(lang, _STRINGS["en"])
