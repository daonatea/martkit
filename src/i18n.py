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
        "window_title": "markIT",
    },
}


def load_strings() -> dict[str, str]:
    lang = QLocale.system().name()[:2].lower()
    return _STRINGS.get(lang, _STRINGS["en"])
