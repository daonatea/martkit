@echo off
setlocal

echo =^> Activating venv
call .venv\Scripts\activate.bat

echo =^> Generating icons
python scripts\make_icon.py

echo =^> Building markIT.exe
python -m PyInstaller ^
    --windowed ^
    --onedir ^
    --name "markIT" ^
    --icon "assets\markIT.ico" ^
    --paths src ^
    --hidden-import markitdown ^
    --hidden-import markitdown._base_converter ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtGui ^
    --collect-all markitdown ^
    --collect-data magika ^
    --noconfirm ^
    src\main.py

echo.
echo =^> Done!
echo     App: dist\markIT\markIT.exe
