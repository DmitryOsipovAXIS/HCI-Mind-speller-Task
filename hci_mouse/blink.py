"""Blink detection via eye aspect ratio (EAR)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)


def eye_aspect_ratio(landmarks, indices: tuple[int, ...] = LEFT_EYE) -> float:
    pts = np.array([(landmarks[i].x, landmarks[i].y) for i in indices], dtype=np.float64)
    vertical = np.linalg.norm(pts[1] - pts[5]) + np.linalg.norm(pts[2] - pts[4])
    horizontal = np.linalg.norm(pts[0] - pts[3])
    if horizontal < 1e-6:
        return 1.0
    return float(vertical / (2.0 * horizontal))


def mean_ear(landmarks) -> float:
    return (eye_aspect_ratio(landmarks, LEFT_EYE) + eye_aspect_ratio(landmarks, RIGHT_EYE)) / 2.0


@dataclass
class BlinkDetector:
    ear_threshold: float
    consec_frames: int
    cooldown_s: float
    _closed_frames: int = field(default=0, init=False)
    _last_click: float = field(default=0.0, init=False)
    last_ear: float | None = field(default=None, init=False)

    def update(self, landmarks) -> bool:
        """Fire once when eyes reopen after a closed interval (classic EAR blink)."""
        self.last_ear = mean_ear(landmarks)

        if self.last_ear < self.ear_threshold:
            self._closed_frames += 1
            return False

        blinked = self._closed_frames >= self.consec_frames
        self._closed_frames = 0

        now = time.perf_counter()
        if blinked and (now - self._last_click) >= self.cooldown_s:
            self._last_click = now
            return True
        return False
