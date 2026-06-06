"""Entrada serverless para desplegar Nexus-Corp SDBCC en Vercel."""

from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "nexus_corp_kbdss"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app import app as app  # noqa: E402,F401
