import ocr


def test_is_image_detects_extensions():
    assert ocr.is_image("/foto.png")
    assert ocr.is_image("/FOTO.JPG")
    assert ocr.is_image("/x.webp")
    assert not ocr.is_image("/doc.pdf")
    assert not ocr.is_image("/audio.mp3")


def test_ocr_image_joins_lines(monkeypatch):
    class FakeEngine:
        def __call__(self, path):
            # RapidOCR devuelve (result, elapse); result = [[box, text, score], ...]
            return ([[None, "Hola", 0.99], [None, "mundo", 0.98]], None)

    monkeypatch.setattr(ocr, "_get_engine", lambda: FakeEngine())
    assert ocr.ocr_image("/x.png") == "Hola\nmundo"


def test_ocr_image_empty_when_no_text(monkeypatch):
    class FakeEngine:
        def __call__(self, path):
            return (None, None)

    monkeypatch.setattr(ocr, "_get_engine", lambda: FakeEngine())
    assert ocr.ocr_image("/x.png") == ""
