"""
OPENCV + MEDIAPIPE - membaca webcam & mendeteksi tangan (thread terpisah).
Hasil: posisi telunjuk (kursor), status cubit (jempol+telunjuk), jumlah jari, frame preview.
"""

import math
import os
import threading
import time
import urllib.request

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/1/hand_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hand_landmarker.task")

HAND_CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
                    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
                    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

PINCH_ON = 0.30     # rasio jarak jempol-telunjuk / ukuran telapak: di bawah ini = cubit
PINCH_OFF = 0.50    # di atas ini = lepas (hysteresis supaya tidak berkedip)


class HandTracker(threading.Thread):
    def __init__(self, cam=0, size=(640, 480), preview=(260, 195)):
        super().__init__(daemon=True)
        self.cam, self.size, self.preview = cam, size, preview
        self.running = True
        self.lock = threading.Lock()
        self.state = dict(ok=False, error=None, status="Membuka kamera...", hand=False,
                          x=0.5, y=0.5, pinch=False, fingers=-1, frame=None, fps=0.0)
        self._pinch = False
        self._detect = None

    # ------------------------------------------------------------ API
    def get(self):
        with self.lock:
            return dict(self.state)

    def stop(self):
        self.running = False

    def _set(self, **kw):
        with self.lock:
            self.state.update(kw)

    # ------------------------------------------------------------ detektor
    def _make_detector(self):
        import mediapipe as mp
        if hasattr(mp, "solutions"):                       # API lama (mudah)
            hands = mp.solutions.hands.Hands(
                max_num_hands=1, model_complexity=0,
                min_detection_confidence=0.6, min_tracking_confidence=0.5)

            def detect(rgb):
                res = hands.process(rgb)
                if res.multi_hand_landmarks:
                    return [(p.x, p.y) for p in res.multi_hand_landmarks[0].landmark]
                return None
            return detect

        # API baru (Tasks) - perlu file model
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
        if not os.path.exists(MODEL_PATH):
            self._set(status="Mengunduh model tangan...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        opts = vision.HandLandmarkerOptions(
            base_options=mpp.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE, num_hands=1,
            min_hand_detection_confidence=0.6, min_tracking_confidence=0.5)
        det = vision.HandLandmarker.create_from_options(opts)

        def detect(rgb):
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = det.detect(img)
            if res.hand_landmarks:
                return [(p.x, p.y) for p in res.hand_landmarks[0]]
            return None
        return detect

    # ------------------------------------------------------------ fitur gestur
    @staticmethod
    def _d(a, b, w, h):
        return math.hypot((a[0] - b[0]) * w, (a[1] - b[1]) * h)

    def _features(self, lm, w, h):
        palm = max(self._d(lm[0], lm[9], w, h), 1e-6)
        ratio = self._d(lm[4], lm[8], w, h) / palm
        if self._pinch:
            self._pinch = ratio < PINCH_OFF
        else:
            self._pinch = ratio < PINCH_ON
        # jari terbuka: ujung jari lebih jauh dari pergelangan dibanding sendi PIP
        fingers = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if self._d(lm[tip], lm[0], w, h) > self._d(lm[pip], lm[0], w, h) * 1.15:
                fingers += 1
        return self._pinch, fingers

    # ------------------------------------------------------------ gambar preview
    def _preview(self, frame, lm, pinch):
        import cv2
        h, w = frame.shape[:2]
        if lm:
            pts = [(int(x * w), int(y * h)) for x, y in lm]
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (80, 220, 120), 2)
            for p in pts:
                cv2.circle(frame, p, 3, (255, 255, 255), -1)
            cv2.circle(frame, pts[8], 10, (0, 0, 255) if pinch else (0, 255, 255), 2)
            cv2.line(frame, pts[4], pts[8], (0, 0, 255) if pinch else (255, 200, 0), 2)
        small = cv2.resize(frame, self.preview, interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    # ------------------------------------------------------------ loop utama
    def run(self):
        try:
            import cv2
            self._detect = self._make_detector()
            backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
            cap = cv2.VideoCapture(self.cam, backend)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])
            if not cap.isOpened():
                raise RuntimeError(f"Kamera #{self.cam} tidak bisa dibuka")
        except Exception as ex:                       # noqa: BLE001
            self._set(error=str(ex), status="Gestur nonaktif: " + str(ex))
            return

        self._set(ok=True, status="Kamera aktif")
        last, fps = time.time(), 0.0
        while self.running:
            okr, frame = cap.read()
            if not okr:
                time.sleep(0.01)
                continue
            frame = cv2.flip(frame, 1)                # mirror: gerak kanan = kursor kanan
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                lm = self._detect(rgb)
            except Exception as ex:                   # noqa: BLE001
                self._set(error=str(ex), ok=False, status="Error deteksi: " + str(ex))
                break
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-3)
            last = now
            if lm:
                pinch, fingers = self._features(lm, w, h)
                self._set(hand=True, x=lm[8][0], y=lm[8][1], pinch=pinch, fingers=fingers,
                          frame=self._preview(frame, lm, pinch), fps=fps,
                          status="Tangan terdeteksi")
            else:
                self._pinch = False
                self._set(hand=False, pinch=False, fingers=-1,
                          frame=self._preview(frame, None, False), fps=fps,
                          status="Tangan tidak terlihat")
        cap.release()
