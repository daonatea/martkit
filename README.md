# markIT

Desktop app for macOS and Windows that converts documents and media files to Markdown using Microsoft's [markitdown](https://github.com/microsoft/markitdown) library.

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black?logo=apple)
![Windows](https://img.shields.io/badge/Windows-10%2F11-blue?logo=windows)
![License](https://img.shields.io/badge/license-MIT-green)

## Supported formats

| Category | Formats |
|---|---|
| Documents | PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx) |
| Web | HTML |
| Audio | MP3, WAV, M4A (transcribed via SpeechRecognition) |
| Email | Outlook (.msg) |
| Video | YouTube URLs (transcript extraction) |

## Download

Go to [Releases](../../releases) and download the latest version for your platform:

- **macOS Apple Silicon** (M1/M2/M3/M4): `markIT-macOS-ARM.dmg`
- **macOS Intel** (2020 and earlier): `markIT-macOS-Intel.dmg`
- **Windows** (10/11 64-bit): `markIT-Windows.zip` → extract and run `markIT.exe`

### Windows installation note

Windows may show a SmartScreen warning on first launch ("Windows protected your PC"). This is expected for open-source apps without a paid certificate. To run:

1. Click **More info**
2. Click **Run anyway**

The app is open source — you can review all source code in this repository.

## Build from source

### Requirements

- Python 3.12
- PyQt6
- Dependencies in `requirements.txt`

### macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./build.sh
```

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
build-windows.bat
```

## Tech stack

- **Python 3.12** — runtime
- **PyQt6** — UI framework
- **markitdown 0.1.6** — document conversion engine (Microsoft)
- **PyInstaller** — standalone executable bundler

## License

MIT — see [LICENSE](LICENSE).

## Code signing

Windows binaries are submitted for signing through [SignPath Foundation](https://signpath.org) (application in progress). See [docs/code-signing-policy.md](docs/code-signing-policy.md).
