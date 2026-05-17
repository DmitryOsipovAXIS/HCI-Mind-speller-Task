"""Runtime defaults; override via CLI in main.py."""

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 0 = raw tracking, 1 = heavy smoothing (higher latency)
SMOOTHING_ALPHA = 0.35

# Margins shrink the active mapping zone (fraction of frame)
MARGIN_X = 0.08
MARGIN_Y = 0.12

# head: nose tip | hand: index fingertip
DEFAULT_TRACK_MODE = "head"

# Eye aspect ratio blink detection (Soukupová & Čech)
EAR_THRESHOLD = 0.21
EAR_CONSEC_FRAMES = 2
CLICK_COOLDOWN_S = 0.45

# MediaPipe
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.5
