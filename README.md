# HCI-Mind-speller-Task

A local **Python webcam HCI** application for the MindSpeller project. It moves the system mouse cursor using your **head** or **hand**, and performs a **left-click** when you **blink**.

Two stacks can coexist in this repo over time:

| Stack | Role |
|-------|------|
| **MediaPipe (current)** | Stable, real-time tracking with pre-trained Google models |
| **Custom YOLO (planned)** | Optional research/demo branch to show a full CV training pipeline |

This README documents the **MediaPipe** implementation that is implemented today.

---

## What it does

1. Captures video from a standard webcam (default 640×480).
2. Tracks a body feature each frame:
   - **Head mode** — nose tip landmark → cursor position.
   - **Hand mode** — index fingertip → cursor position.
3. Detects blinks via **Eye Aspect Ratio (EAR)** on face landmarks → `pynput` left-click.
4. Shows an optional preview window with landmarks, EAR value, and click feedback.

---

## Requirements

- **OS:** Windows (tested; paths use `%LOCALAPPDATA%` for model files).
- **Python:** 3.10+ (3.11 recommended).
- **Hardware:** Webcam; the app controls the real mouse — use a safe desktop area for testing.
- **Permissions:** Camera access; no admin required for normal use.

---

## Project structure

```text
HCI-Mind-speller-Task/
├── run.py                 # Start the app from the project root
├── requirements.txt       # Python dependencies (OpenCV, MediaPipe, …)
├── README.md              # This file
├── .gitignore             # Ignores .venv, __pycache__, etc.
│
├── models/                # Optional local copies of MediaPipe .task bundles
│   ├── face_landmarker.task
│   └── hand_landmarker.task
│
└── hci_mouse/             # Main application package
    ├── __init__.py        # Package version marker
    ├── main.py            # CLI, webcam loop, wiring of all modules
    ├── config.py          # Default thresholds and camera settings
    ├── tracker.py         # MediaPipe face/hand landmark detection
    ├── blink.py           # EAR-based blink detector
    ├── mouse_controller.py# Screen mapping, smoothing, mouse move/click
    └── models_util.py     # Download/copy models to an ASCII-safe path
```

### Root files

| File | Purpose |
|------|---------|
| `run.py` | Thin entry point. Run `python run.py` from the project root. |
| `requirements.txt` | Pins libraries: `opencv-python`, `mediapipe`, `numpy`, `pynput`. |
| `.gitignore` | Keeps virtualenv and bytecode out of git. |
| `README.md` | Project overview, setup, and usage. |

### `models/` directory

| File | Purpose |
|------|---------|
| `face_landmarker.task` | Pre-trained MediaPipe face mesh model (~3.6 MB). Used for landmarks and blink (eyes). |
| `hand_landmarker.task` | Pre-trained MediaPipe hand model (~7.8 MB). Used in `--mode hand`. |

On first run, these files are **copied** from `models/` (if present) or **downloaded** into:

`%LOCALAPPDATA%\hci_mouse_models\`

That avoids load failures when the project path contains non-ASCII characters (e.g. Cyrillic folder names on Windows).

### `hci_mouse/` package

| Module | Purpose |
|--------|---------|
| `main.py` | Opens the camera, runs the frame loop, parses CLI flags, prints average FPS on exit. |
| `config.py` | Central defaults: resolution, smoothing, EAR threshold, detection confidence. |
| `tracker.py` | Wraps MediaPipe **FaceLandmarker** and **HandLandmarker** (Tasks API). Returns normalized `(x, y)` and landmark lists. |
| `blink.py` | Computes EAR from eye landmarks; fires one click when eyes reopen after a short closed interval. |
| `mouse_controller.py` | Maps normalized camera coordinates to screen pixels with margins and exponential smoothing; sends clicks via `pynput`. |
| `models_util.py` | Resolves model paths, downloads from Google storage if needed. |
| `__init__.py` | Package metadata (`__version__`). |

### Generated / local (not in git)

| Path | Purpose |
|------|---------|
| `.venv/` | Python virtual environment after `python -m venv .venv`. |
| `hci_mouse/__pycache__/` | Bytecode cache created at import time. |
| `%LOCALAPPDATA%\hci_mouse_models\` | Runtime copy of `.task` models used by MediaPipe. |

---

## How the pipeline works

```text
Webcam → OpenCV frame (mirrored)
       → MediaPipe FaceLandmarker (always, for blink + head mode)
       → MediaPipe HandLandmarker (hand mode only)
       → BlinkDetector (EAR) → left click if blink
       → MouseMapper → cursor position
       → Optional preview window
```

- **Cursor:** landmark position is normalized to `[0, 1]` then mapped to the screen with edge margins and smoothing.
- **Click:** both eyes must be closed for a few frames; click fires when they open again (with a cooldown to avoid double-clicks).

---

## Setup (first time)

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first application start may print `Downloading face_landmarker.task ...` while models are fetched (~12 MB total).

---

## When and how to run

### When to use

| Situation | Command |
|-----------|---------|
| Default demo / head control | `python run.py` |
| Point with your index finger | `python run.py --mode hand` |
| Lower latency (no overlay window) | `python run.py --no-preview` |
| Blinks not registering | `python run.py --ear-threshold 0.18` |
| Cursor too jittery | `python run.py --smoothing 0.5` |
| Wrong webcam | `python run.py --camera 1` |

Always activate the virtual environment first:

```powershell
.venv\Scripts\activate
python run.py
```

Or call the venv Python directly (as in VS Code / Cursor):

```powershell
.venv\Scripts\python.exe run.py
```

### Controls

| Input | Action |
|-------|--------|
| Move head (nose) or index finger | Move mouse cursor |
| Blink (both eyes) | Left mouse click |
| **Q** or **Esc** | Quit |

### CLI reference

```text
python run.py [-h] [--mode {head,hand}] [--camera CAMERA]
              [--no-preview] [--smoothing SMOOTHING]
              [--ear-threshold EAR_THRESHOLD]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--mode head` | `head` | `head` = nose tip; `hand` = index fingertip (face still needed for blinks). |
| `--camera` | `0` | Webcam device index. |
| `--no-preview` | off | Skip OpenCV preview for slightly lower latency. |
| `--smoothing` | `0.35` | `0` = raw tracking; higher = smoother but more lag. |
| `--ear-threshold` | `0.21` | Lower = easier blink detection (may increase false clicks). |

### Tuning via `config.py`

Edit `hci_mouse/config.py` to change defaults without CLI flags:

- `FRAME_WIDTH`, `FRAME_HEIGHT` — capture resolution.
- `SMOOTHING_ALPHA`, `MARGIN_X`, `MARGIN_Y` — cursor feel and usable area.
- `EAR_THRESHOLD`, `EAR_CONSEC_FRAMES`, `CLICK_COOLDOWN_S` — blink behavior.
- `MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE` — tracking stability vs sensitivity.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `Could not open webcam` | Close other apps using the camera; try `--camera 1`. |
| `module 'mediapipe' has no attribute 'solutions'` | Use `mediapipe>=0.10.30` from `requirements.txt` (Tasks API). |
| Model file / path errors on Windows | Let the app download to `%LOCALAPPDATA%\hci_mouse_models`; or copy `.task` files into `models/`. |
| Clicks too hard / too easy | Adjust `--ear-threshold` (try `0.18`–`0.24`). |
| Cursor jumps | Increase `--smoothing`; ensure good lighting and face/hand fully in frame. |
| Hand mode: no clicks | Keep your face visible so eye landmarks are detected. |

---

## Dependencies (summary)

| Package | Role |
|---------|------|
| `opencv-python` | Webcam capture and preview window |
| `mediapipe` | Pre-trained face/hand landmark models (Tasks API) |
| `numpy` | EAR geometry math |
| `pynput` | OS mouse move and click |

You do **not** need to train these models for the current app — they are pre-trained by Google.

---

## License / context

Human–Computer Interface coursework for **MindSpeller**. For a future custom **YOLO** branch, keep it as a separate script or `--backend` flag so this stable MediaPipe path remains the reference implementation.
