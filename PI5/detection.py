import time, threading, requests
from ultralytics import YOLO
import cv2
import numpy as np

class Detector:
    def __init__(self, viewer, config):
        self.viewer = viewer
        self.config = config
        self.running = False

        # Load YOLO model
        self.model = YOLO("yolo11n.pt")

        # YOLO → UI overlay storage
        self.last_boxes = []

        # Spray logic
        self.last_trigger = 0
        self.cooldown = 10          # seconds between sprays
        self.spray_duration = 5      # relay ON duration

        self.update_target_objects()

    # ------------------------------------
    # Load user-selected detection classes
    # ------------------------------------
    def update_target_objects(self):
        lst = self.config.get("detect_objects", ["cat","person"]) # remove person here
        self.target_objects = set(lst)

    def update_config(self, cfg):
        self.config = cfg
        self.update_target_objects()

    # ------------------------------------
    # ESP32 Spray Trigger
    # ------------------------------------
    def trigger_spray(self):
        esp = self.config["esp32_ip"]
        url_on = f"http://{esp}/relay/on"
        url_off = f"http://{esp}/relay/off"

        try:
            print("[ACTION] Spray ON")
            requests.get(url_on, timeout=1)
        except:
            print("[WARN] Spray ON failed")

        time.sleep(self.spray_duration)

        try:
            print("[ACTION] Spray OFF")
            requests.get(url_off, timeout=1)
        except:
            print("[WARN] Spray OFF failed")

    # ------------------------------------
    # Start/Stop detection
    # ------------------------------------
    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        self.running = False

    # ------------------------------------
    # Helper: Distance of point → line segment
    # ------------------------------------
    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        line_mag = np.hypot(x2 - x1, y2 - y1)
        if line_mag < 1e-6:
            return 9999

        # Projection of point onto line segment
        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)
        u = max(0, min(1, u))

        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)

        return np.hypot(px - ix, py - iy)

    # ------------------------------------
    # YOLO detection loop
    # ------------------------------------
    def loop(self):
        print("[INFO] Detection started")

        while self.running:
            frame = self.viewer.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            h, w = frame.shape[:2]

            # Read user line
            line = self.config.get("line", [])
            if len(line) == 4:
                lx1 = int(line[0] * w)
                ly1 = int(line[1] * h)
                lx2 = int(line[2] * w)
                ly2 = int(line[3] * h)
            else:
                lx1 = ly1 = lx2 = ly2 = None

            # --------------------------
            # YOLO inference
            # --------------------------
            results = self.model(frame, imgsz=640)

            boxes_out = []   # for UI overlay

            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    name = self.model.names[cls]
                    conf = float(box.conf[0])

                    # box coords
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))

                    # Save box for UI
                    boxes_out.append({
                        "cls": name,
                        "conf": conf,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    })

                    # --------------------------
                    # LINE-CROSS DETECTION
                    # --------------------------
                    if lx1 is not None and name in self.target_objects:

                        obj_x = int((x1 + x2) / 2)   # midpoint X
                        obj_y = int(y2)              # bottom of bounding box

                        # Distance threshold (px)
                        dist = self.point_to_line_distance(
                            obj_x, obj_y,
                            lx1, ly1, lx2, ly2
                        )

                        if dist < 25:  # looks "touching the line"
                            if time.time() - self.last_trigger > self.cooldown:
                                print("[TRIGGER] Line crossed by:", name)
                                self.last_trigger = time.time()
                                threading.Thread(
                                    target=self.trigger_spray,
                                    daemon=True
                                ).start()

            # Update UI bounding boxes
            self.last_boxes = boxes_out

        print("[INFO] Detection stopped")
