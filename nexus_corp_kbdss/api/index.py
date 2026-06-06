"""Entrada serverless si Vercel usa nexus_corp_kbdss como carpeta raíz."""

from pathlib import Path
import sys


APP_DIR = Path(__file__).resolve().parents[1]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app import app as app  # noqa: E402,F401
