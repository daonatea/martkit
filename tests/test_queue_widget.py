STRINGS = {
    "queue_header": "Files", "queue_clear": "Clear",
    "status_waiting": "Waiting", "status_converting": "Converting",
    "status_done": "Done", "status_error": "Error",
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
