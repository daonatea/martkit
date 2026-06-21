#!/usr/bin/env bash
set -e

echo "==> Activating venv"
source .venv/bin/activate

echo "==> Installing PyInstaller"
pip install -q pyinstaller

echo "==> Building Markiti.app"
pyinstaller \
    --windowed \
    --onedir \
    --name "Markiti" \
    --paths src \
    --hidden-import markitdown \
    --hidden-import markitdown._base_converter \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtGui \
    --collect-all markitdown \
    --noconfirm \
    src/main.py

echo ""
echo "==> Fixing code signature (ditto --norsrc strips resource forks)"
ditto --norsrc dist/Markiti.app /tmp/Markiti_signed.app
codesign -s - --force --deep /tmp/Markiti_signed.app
rm -rf dist/Markiti.app
mv /tmp/Markiti_signed.app dist/Markiti.app
codesign --verify --deep dist/Markiti.app && echo "==> Firma OK"

echo ""
echo "==> Done! App built at: dist/Markiti.app"
echo "==> To install: cp -r dist/Markiti.app /Applications/"
echo "==> First run: right-click → Open (Gatekeeper bypass, one time only)"
