import transcribe


def test_is_audio_detects_extensions():
    assert transcribe.is_audio("/a.mp3")
    assert transcribe.is_audio("/A.WAV")
    assert not transcribe.is_audio("/a.png")


def test_is_model_cached_false_when_dir_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "MODEL_DIR", tmp_path)
    assert transcribe.is_model_cached() is False


def test_is_model_cached_true_when_model_bin_present(tmp_path, monkeypatch):
    monkeypatch.setattr(transcribe, "MODEL_DIR", tmp_path)
    nested = tmp_path / "models--Systran--faster-whisper-base" / "snapshots" / "abc"
    nested.mkdir(parents=True)
    (nested / "model.bin").write_bytes(b"x")
    assert transcribe.is_model_cached() is True


def test_transcribe_audio_returns_body(monkeypatch):
    class Seg:
        def __init__(self, text):
            self.text = text

    class FakeModel:
        def transcribe(self, path):
            class Info:
                language = "es"
            return ([Seg(" Hola "), Seg(" mundo ")], Info())

    monkeypatch.setattr(transcribe, "_get_model", lambda: FakeModel())
    assert transcribe.transcribe_audio("/a.mp3") == "Hola\n\nmundo"
