@echo off
title WorkspaceAI
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [WorkspaceAI] Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [WorkspaceAI] Installing / checking dependencies...
pip install -r requirements.txt --quiet

echo [WorkspaceAI] Launching...
python main.py
pause
