from unittest.mock import patch

REQUIRED_KEYS = [
    "drop_hint", "drop_sub", "btn_select", "btn_convert", "btn_cancel",
    "btn_open_folder", "status_waiting", "status_converting", "status_done",
    "status_error", "folder_label", "folder_change", "queue_clear",
    "queue_header", "counter", "window_title",
    "status_warning", "status_skipped", "warn_no_content",
    "audio_dl_title", "audio_dl_body", "audio_dl_accept", "audio_dl_skip",
]

def test_spanish_locale(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "es_ES"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convertir todo →"
        assert strings["status_done"] == "Listo"

def test_english_locale(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "en_US"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convert all →"
        assert strings["status_done"] == "Done"

def test_unknown_locale_falls_back_to_english(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "fr_FR"
        import i18n
        strings = i18n.load_strings()
        assert strings["btn_convert"] == "Convert all →"

def test_all_required_keys_present():
    import i18n
    for lang, lang_strings in i18n._STRINGS.items():
        for key in REQUIRED_KEYS:
            assert key in lang_strings, f"Missing key '{key}' in lang '{lang}'"

def test_counter_template_interpolates(qapp):
    with patch("i18n.QLocale") as MockLocale:
        MockLocale.system.return_value.name.return_value = "es_ES"
        import i18n
        strings = i18n.load_strings()
        result = strings["counter"].format(done=2, total=5)
        assert result == "2 / 5 listos"
