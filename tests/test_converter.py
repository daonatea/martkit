from pathlib import Path


def test_converts_text_file(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    worker = ConvertWorker([tmp_txt], str(out_dir))

    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()

    assert len(finished) == 1
    out_file = Path(finished[0])
    assert out_file.exists()
    assert out_file.suffix == ".md"
    assert out_file.stem == "sample"


def test_converts_html_file(qapp, tmp_html, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    worker = ConvertWorker([tmp_html], str(out_dir))

    finished = []
    worker.file_finished.connect(lambda p, out: finished.append(out))
    worker.run()

    assert len(finished) == 1
    content = Path(finished[0]).read_text(encoding="utf-8")
    assert "Hello" in content


def test_emits_error_on_missing_file(qapp, tmp_path):
    from converter import ConvertWorker
    worker = ConvertWorker(["/nonexistent/file.xyz"], str(tmp_path / "out"))

    errors = []
    worker.file_error.connect(lambda p, e: errors.append((p, e)))
    worker.run()

    assert len(errors) == 1
    assert "nonexistent" in errors[0][0]


def test_cancel_before_run_skips_all(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    worker = ConvertWorker([tmp_txt], str(tmp_path / "out"))
    worker.cancel()

    started = []
    worker.file_started.connect(lambda p: started.append(p))
    worker.run()

    assert len(started) == 0


def test_creates_output_dir_if_missing(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "deep" / "nested" / "output"
    assert not out_dir.exists()
    worker = ConvertWorker([tmp_txt], str(out_dir))
    worker.run()
    assert out_dir.exists()


def test_overwrites_existing_md(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    existing = out_dir / "sample.md"
    existing.write_text("OLD CONTENT", encoding="utf-8")

    worker = ConvertWorker([tmp_txt], str(out_dir))
    worker.run()

    assert existing.read_text(encoding="utf-8") != "OLD CONTENT"


def test_all_done_emitted(qapp, tmp_txt, tmp_path):
    from converter import ConvertWorker
    done_called = []
    worker = ConvertWorker([tmp_txt], str(tmp_path / "out"))
    worker.all_done.connect(lambda: done_called.append(True))
    worker.run()
    assert done_called == [True]
