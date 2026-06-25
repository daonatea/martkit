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
