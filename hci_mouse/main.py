"""Webcam HCI: body-feature cursor control + blink to click."""

from __future__ import annotations

import argparse
import sys
import time

import cv2

from hci_mouse import config
from hci_mouse.blink import BlinkDetector
from hci_mouse.mouse_controller import MouseMapper
from hci_mouse.tracker import BodyTracker


def _screen_size() -> tuple[int, int]:
    try:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


def _open_camera(index: int, width: int, height: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def run(
    *,
    mode: str,
    camera: int,
    preview: bool,
    smoothing: float,
    ear_threshold: float,
) -> int:
    cap = _open_camera(camera, config.FRAME_WIDTH, config.FRAME_HEIGHT)
    if not cap.isOpened():
        print("Error: could not open webcam.", file=sys.stderr)
        return 1

    sw, sh = _screen_size()
    mapper = MouseMapper(
        screen_w=sw,
        screen_h=sh,
        margin_x=config.MARGIN_X,
        margin_y=config.MARGIN_Y,
        smoothing=smoothing,
    )
    tracker = BodyTracker(mode)
    blink = BlinkDetector(
        ear_threshold=ear_threshold,
        consec_frames=config.EAR_CONSEC_FRAMES,
        cooldown_s=config.CLICK_COOLDOWN_S,
    )

    print("HCI mouse active. Blink to left-click. Press Q or Esc to quit.")
    if mode == "hand":
        print("Hand mode: point with index finger; keep face visible for blinks.")

    frames = 0
    t0 = time.perf_counter()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            result = tracker.process(frame)

            did_blink = False
            if result.landmarks is not None:
                if blink.update(result.landmarks):
                    mapper.click()
                    did_blink = True

            if result.track_xy is not None:
                mapper.move(*result.track_xy)

            if preview:
                overlay = tracker.draw_preview(
                    frame,
                    result,
                    blink.last_ear,
                    did_blink,
                )
                cv2.imshow("HCI Mouse", overlay)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

            frames += 1
    finally:
        elapsed = time.perf_counter() - t0
        if elapsed > 0 and frames > 0:
            print(f"Average FPS: {frames / elapsed:.1f}")
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Webcam HCI: track head or hand to move the mouse; blink to click.",
    )
    parser.add_argument(
        "--mode",
        choices=("head", "hand"),
        default=config.DEFAULT_TRACK_MODE,
        help="Body feature used for cursor (default: head)",
    )
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX)
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Disable preview window for lower latency",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=config.SMOOTHING_ALPHA,
        help="Cursor smoothing 0..1 (higher = smoother, more lag)",
    )
    parser.add_argument(
        "--ear-threshold",
        type=float,
        default=config.EAR_THRESHOLD,
        help="Blink sensitivity; lower = easier to trigger",
    )
    args = parser.parse_args(argv)

    return run(
        mode=args.mode,
        camera=args.camera,
        preview=not args.no_preview,
        smoothing=max(0.0, min(1.0, args.smoothing)),
        ear_threshold=args.ear_threshold,
    )


if __name__ == "__main__":
    raise SystemExit(main())
