"""Locate or download MediaPipe .task models on an ASCII-safe path."""

from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

FACE_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
HAND_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

_MODELS = {
    "face_landmarker.task": FACE_URL,
    "hand_landmarker.task": HAND_URL,
}


def _model_store_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or str(Path.home())
    return Path(base) / "hci_mouse_models"


def _bundle_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "models"


def ensure_model(name: str) -> str:
    """Return absolute path to a model file, downloading or copying if needed."""
    if name not in _MODELS:
        raise ValueError(f"Unknown model: {name}")

    store = _model_store_dir()
    store.mkdir(parents=True, exist_ok=True)
    target = store / name

    if target.is_file() and target.stat().st_size > 0:
        return str(target)

    bundled = _bundle_dir() / name
    if bundled.is_file():
        shutil.copy2(bundled, target)
        return str(target)

    print(f"Downloading {name} ...")
    tmp = target.with_suffix(".part")
    try:
        urllib.request.urlretrieve(_MODELS[name], tmp)
        tmp.replace(target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    return str(target)
