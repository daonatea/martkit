def test_main_window_opens(qapp):
    from window import MainWindow
    w = MainWindow()
    w.show()
    assert w.isVisible()
    assert w.width() == 640
    assert w.height() == 460
    w.close()
