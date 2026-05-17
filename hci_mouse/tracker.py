"""MediaPipe Tasks API: face / hand tracking (single pass per frame)."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options as base_options_module
from mediapipe.tasks.python.vision import (
    FaceLandmarksConnections,
    HandLandmarksConnections,
    drawing_styles,
    drawing_utils,
)

from hci_mouse import config
from hci_mouse.models_util import ensure_model

NOSE_TIP = 1
INDEX_TIP = 8

BaseOptions = base_options_module.BaseOptions


@dataclass
class TrackFrame:
    track_xy: tuple[float, float] | None
    landmarks: list | None
    face_landmarks: list | None
    hand_landmarks: list | None


class BodyTracker:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self._timestamp_ms = 0

        face_opts = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=ensure_model("face_landmarker.task")),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_face_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self._face = vision.FaceLandmarker.create_from_options(face_opts)

        self._hands: vision.HandLandmarker | None = None
        if mode == "hand":
            hand_opts = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=ensure_model("hand_landmarker.task")),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=config.MAX_NUM_HANDS,
                min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
                min_hand_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
                min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
            )
            self._hands = vision.HandLandmarker.create_from_options(hand_opts)

    def close(self) -> None:
        self._face.close()
        if self._hands is not None:
            self._hands.close()

    def _next_timestamp(self) -> int:
        self._timestamp_ms += 33
        return self._timestamp_ms

    @staticmethod
    def _to_mp_image(frame_bgr: np.ndarray) -> Image:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return Image(image_format=ImageFormat.SRGB, data=np.ascontiguousarray(rgb))

    def process(self, frame_bgr: np.ndarray) -> TrackFrame:
        mp_image = self._to_mp_image(frame_bgr)
        ts = self._next_timestamp()

        track_xy: tuple[float, float] | None = None
        landmarks = None
        face_lm = None
        hand_list: list | None = None

        face_result = self._face.detect_for_video(mp_image, ts)
        if face_result.face_landmarks:
            face_lm = face_result.face_landmarks[0]
            landmarks = face_lm
            if self.mode == "head":
                pt = face_lm[NOSE_TIP]
                track_xy = (pt.x, pt.y)

        if self.mode == "hand" and self._hands is not None:
            hand_result = self._hands.detect_for_video(mp_image, ts)
            if hand_result.hand_landmarks:
                hand_list = hand_result.hand_landmarks
                pt = hand_list[0][INDEX_TIP]
                track_xy = (pt.x, pt.y)

        return TrackFrame(track_xy, landmarks, face_lm, hand_list)

    def draw_preview(
        self,
        frame_bgr: np.ndarray,
        result: TrackFrame,
        ear: float | None,
        blinked: bool,
    ) -> np.ndarray:
        out = frame_bgr.copy()
        h, w = out.shape[:2]

        if result.face_landmarks is not None:
            drawing_utils.draw_landmarks(
                out,
                result.face_landmarks,
                FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS,
                None,
                drawing_styles.get_default_face_mesh_contours_style(),
            )

        if result.hand_landmarks:
            for hl in result.hand_landmarks:
                drawing_utils.draw_landmarks(
                    out,
                    hl,
                    HandLandmarksConnections.HAND_CONNECTIONS,
                    drawing_styles.get_default_hand_landmarks_style(),
                    drawing_styles.get_default_hand_connections_style(),
                )

        if result.track_xy is not None:
            px, py = int(result.track_xy[0] * w), int(result.track_xy[1] * h)
            cv2.circle(out, (px, py), 10, (0, 255, 0), 2)

        status = f"mode={self.mode}"
        if ear is not None:
            status += f"  EAR={ear:.2f}"
        if blinked:
            status += "  CLICK"
        cv2.putText(
            out,
            status,
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return out
