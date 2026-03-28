#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "[WorkspaceAI] Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "[WorkspaceAI] Installing / checking dependencies..."
pip install -r requirements.txt --quiet

echo "[WorkspaceAI] Launching in demo mode (non-Windows)..."
python main.py
