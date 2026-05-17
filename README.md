# HCI-Mind-speller-Task

Webcam-based HCI: move the mouse with your **head** (nose) or **hand** (index finger), and **blink** to left-click.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On first run, face/hand model files are copied (or downloaded) to `%LOCALAPPDATA%\hci_mouse_models` so MediaPipe can load them on Windows paths with non-ASCII characters.

## Run

```bash
python run.py
python run.py --mode hand
python run.py --no-preview
```

Press **Q** or **Esc** to quit. Tune blink sensitivity with `--ear-threshold` (default `0.21`; lower = easier clicks).
