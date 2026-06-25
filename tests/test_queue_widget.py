STRINGS = {
    "queue_header": "Files", "queue_clear": "Clear",
    "status_waiting": "Waiting", "status_converting": "Converting",
    "status_done": "Done", "status_error": "Error",
    "status_warning": "No content", "status_skipped": "Skipped",
    "warn_no_content": "The file had no content to convert.",
}


def test_add_files_shows_rows(qapp, tmp_txt):
    from queue_model import FileQueueModel
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    assert m.total() == 1


def test_update_status_done(qapp, tmp_txt):
    from queue_model import FileQueueModel, FileStatus
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    w.update_status(tmp_txt, FileStatus.DONE)
    assert m.items()[0].status == FileStatus.DONE


def test_waiting_paths_after_done(qapp, tmp_txt):
    from queue_model import FileQueueModel, FileStatus
    from queue_widget import QueueWidget
    m = FileQueueModel()
    w = QueueWidget(m, STRINGS)
    w.add_files([tmp_txt])
    w.update_status(tmp_txt, FileStatus.DONE)
    assert w.waiting_paths() == []


def test_warning_and_skipped_render(qapp):
    from queue_widget import QueueWidget
    from queue_model import FileQueueModel, FileStatus
    from i18n import load_strings

    strings = load_strings()
    model = FileQueueModel()
    w = QueueWidget(model, strings)
    w.add_files(["/a.png", "/b.mp3"])

    w.update_status("/a.png", FileStatus.WARNING, strings["warn_no_content"])
    w.update_status("/b.mp3", FileStatus.SKIPPED)

    row_a = w._rows["/a.png"]
    row_b = w._rows["/b.mp3"]
    assert strings["status_warning"] in row_a._status_lbl.text()
    assert row_a._status_lbl.toolTip() == strings["warn_no_content"]
    assert strings["status_skipped"] in row_b._status_lbl.text()
