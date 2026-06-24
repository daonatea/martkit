def test_main_window_opens(qapp):
    from window import MainWindow
    w = MainWindow()
    w.show()
    assert w.isVisible()
    assert w.width() == 680
    assert w.height() == 480
    w.close()


def test_declined_audio_is_skipped(qapp, monkeypatch):
    import window
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(window, "is_model_cached", lambda: False)
    w = MainWindow()
    # Simula que el usuario rechaza la descarga.
    monkeypatch.setattr(w, "_ask_audio_download", lambda: False)
    w._on_files_added(["/song.mp3", "/doc.pdf"])

    statuses = {i.path: i.status for i in w._model.items()}
    assert statuses["/song.mp3"] == FileStatus.SKIPPED
    assert statuses["/doc.pdf"] == FileStatus.WAITING
    w.close()


def test_accepted_audio_stays_waiting(qapp, monkeypatch):
    import window
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(window, "is_model_cached", lambda: False)
    w = MainWindow()
    monkeypatch.setattr(w, "_ask_audio_download", lambda: True)
    w._on_files_added(["/song.mp3"])

    assert w._model.items()[0].status == FileStatus.WAITING
    w.close()


def test_no_dialog_when_model_cached(qapp, monkeypatch):
    import window
    from window import MainWindow
    from queue_model import FileStatus

    monkeypatch.setattr(window, "is_model_cached", lambda: True)
    called = []
    w = MainWindow()
    monkeypatch.setattr(w, "_ask_audio_download", lambda: called.append(True) or True)
    w._on_files_added(["/song.mp3"])

    assert called == []  # no se preguntó porque ya está en caché
    assert w._model.items()[0].status == FileStatus.WAITING
    w.close()
