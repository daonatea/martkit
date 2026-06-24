#!/usr/bin/env bash
set -e

VENV_BIN="$(pwd)/.venv/bin"
export PATH="$VENV_BIN:$PATH"

echo "==> Generating icon"
"$VENV_BIN/python3" scripts/make_icon.py >/dev/null

echo "==> Building markIT.app"
"$VENV_BIN/python3" -m PyInstaller \
    --windowed \
    --onedir \
    --name "markIT" \
    --icon "assets/markIT.icns" \
    --paths src \
    --hidden-import markitdown \
    --hidden-import markitdown._base_converter \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtGui \
    --hidden-import transcribe \
    --collect-all markitdown \
    --collect-all pdfminer \
    --collect-all pdfplumber \
    --collect-all mammoth \
    --collect-all pptx \
    --collect-all olefile \
    --collect-all faster_whisper \
    --collect-all ctranslate2 \
    --collect-all av \
    --collect-data magika \
    --noconfirm \
    src/main.py

echo ""
echo "==> Fixing code signature (ditto --norsrc strips resource forks)"
ditto --norsrc dist/markIT.app /tmp/markIT_signed.app
codesign -s - --force --deep /tmp/markIT_signed.app
rm -rf dist/markIT.app
mv /tmp/markIT_signed.app dist/markIT.app
codesign --verify --deep dist/markIT.app && echo "==> Firma OK"

echo ""
echo "==> Building DMG installer"
rm -f dist/markIT.dmg
create-dmg \
    --volname "markIT" \
    --volicon "assets/markIT.icns" \
    --window-pos 200 120 \
    --window-size 560 340 \
    --icon-size 128 \
    --icon "markIT.app" 140 170 \
    --hide-extension "markIT.app" \
    --app-drop-link 420 170 \
    --no-internet-enable \
    "dist/markIT.dmg" \
    "dist/markIT.app"

echo ""
echo "==> Done!"
echo "    App:       dist/markIT.app"
echo "    Installer: dist/markIT.dmg"
