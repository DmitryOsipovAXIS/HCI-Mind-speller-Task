"""Map normalized camera coordinates to screen cursor."""

from __future__ import annotations

from dataclasses import dataclass

from pynput.mouse import Button, Controller


@dataclass
class MouseMapper:
    screen_w: int
    screen_h: int
    margin_x: float
    margin_y: float
    smoothing: float

    def __post_init__(self) -> None:
        self._mouse = Controller()
        self._sx: float | None = None
        self._sy: float | None = None

    def _norm_to_screen(self, nx: float, ny: float) -> tuple[int, int]:
        # nx, ny in [0, 1]; margins compress usable range
        span_x = 1.0 - 2.0 * self.margin_x
        span_y = 1.0 - 2.0 * self.margin_y
        x = self.margin_x + nx * span_x
        y = self.margin_y + ny * span_y
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        return int(x * (self.screen_w - 1)), int(y * (self.screen_h - 1))

    def move(self, nx: float, ny: float) -> None:
        tx, ty = self._norm_to_screen(nx, ny)
        if self._sx is None:
            self._sx, self._sy = float(tx), float(ty)
        else:
            a = self.smoothing
            self._sx = a * tx + (1.0 - a) * self._sx
            self._sy = a * ty + (1.0 - a) * self._sy
        self._mouse.position = (int(self._sx), int(self._sy))

    def click(self) -> None:
        self._mouse.click(Button.left, 1)
