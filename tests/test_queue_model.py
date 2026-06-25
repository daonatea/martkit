from queue_model import FileQueueModel, FileStatus, FileItem


def test_add_files_returns_newly_added():
    m = FileQueueModel()
    added = m.add_files(["/a.pdf", "/b.docx"])
    assert added == ["/a.pdf", "/b.docx"]
    assert m.total() == 2


def test_add_files_skips_duplicates():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    added = m.add_files(["/a.pdf", "/b.docx"])
    assert added == ["/b.docx"]
    assert m.total() == 2


def test_clear_empties_queue():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf"])
    m.clear()
    assert m.total() == 0


def test_set_status_updates_item():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    assert m.items()[0].status == FileStatus.DONE


def test_set_status_stores_error():
    m = FileQueueModel()
    m.add_files(["/a.pdf"])
    m.set_status("/a.pdf", FileStatus.ERROR, error="Conversion failed")
    assert m.items()[0].error == "Conversion failed"


def test_waiting_paths_excludes_done():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    assert m.waiting_paths() == ["/b.pdf"]


def test_done_count():
    m = FileQueueModel()
    m.add_files(["/a.pdf", "/b.pdf", "/c.pdf"])
    m.set_status("/a.pdf", FileStatus.DONE)
    m.set_status("/b.pdf", FileStatus.DONE)
    assert m.done_count() == 2


def test_file_item_name():
    assert FileItem("/folder/document.pdf").name == "document.pdf"


def test_file_item_type_icons():
    assert FileItem("/x.pdf").type_icon == "📄"
    assert FileItem("/x.xlsx").type_icon == "📊"
    assert FileItem("/x.docx").type_icon == "📝"
    assert FileItem("/x.pptx").type_icon == "📋"
    assert FileItem("/x.html").type_icon == "🌐"
    assert FileItem("/x.unknown").type_icon == "📄"


def test_file_status_has_warning_and_skipped():
    assert FileStatus.WARNING.value == "warning"
    assert FileStatus.SKIPPED.value == "skipped"


def test_file_item_image_and_text_icons():
    assert FileItem("/x.png").type_icon == "🖼️"
    assert FileItem("/x.jpg").type_icon == "🖼️"
    assert FileItem("/x.jpeg").type_icon == "🖼️"
    assert FileItem("/x.webp").type_icon == "🖼️"
    assert FileItem("/x.txt").type_icon == "📄"
    assert FileItem("/x.md").type_icon == "📄"
