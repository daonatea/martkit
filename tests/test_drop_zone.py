def test_drop_zone_smoke(qapp):
    from drop_zone import DropZone
    strings = {
        "drop_hint": "Drop here", "drop_sub": "or select",
        "btn_select": "Select files…",
    }
    w = DropZone(strings)
    w.show()
    assert w.isVisible()
    w.close()


def test_files_dropped_signal(qapp, tmp_txt):
    from drop_zone import DropZone
    strings = {
        "drop_hint": "Drop here", "drop_sub": "or select",
        "btn_select": "Select files…",
    }
    w = DropZone(strings)
    received = []
    w.files_dropped.connect(lambda paths: received.extend(paths))
    w._emit_files([tmp_txt])
    assert received == [tmp_txt]


def test_supported_exts_cover_images_text_and_drop_legacy():
    from drop_zone import _SUPPORTED_EXTS
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"):
        assert ext in _SUPPORTED_EXTS
    assert ".doc" not in _SUPPORTED_EXTS
    assert ".ppt" not in _SUPPORTED_EXTS
    # Modernos sí permanecen
    assert ".docx" in _SUPPORTED_EXTS
    assert ".pptx" in _SUPPORTED_EXTS
    assert ".xlsx" in _SUPPORTED_EXTS
    assert ".xls" in _SUPPORTED_EXTS
