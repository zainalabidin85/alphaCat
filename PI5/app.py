#!/usr/bin/env python3
from flask import Flask, render_template, Response, request, jsonify
from urllib.parse import quote
import json, threading, time, cv2, os

from videoViewerPi2 import VideoViewerPi
from detection import Detector

CONFIG_PATH = "config.json"

app = Flask(__name__)

# ============================================================
# CONFIG HANDLING
# ============================================================
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

# ============================================================
# CAMERA START / RESTART LOGIC
# ============================================================
viewer = None
detector = None
viewer_thread = None

def usb_camera_exists(dev="/dev/video0"):
	return os.path.exists(dev)
	
def build_camera_input(cam_cfg):
    cam_type = cam_cfg.get("type", "usb")

    # --- RTSP explicitly selected ---
    if cam_type == "rtsp":
        rtsp = cam_cfg.get("rtsp", {})
        url = rtsp.get("url", "").strip()

        if url:
            u = quote(rtsp.get("username", ""), safe="")
            p = quote(rtsp.get("password", ""), safe="")
            if u or p:
                return f"rtsp://{u}:{p}@{url}"
            else:
                return f"rtsp://{url}"

        print("[WARN] RTSP selected but URL missing")

    # --- USB fallback ---
    usb_dev = cam_cfg.get("device", "/dev/video0")
    if usb_camera_exists(usb_dev):
        print("[INFO] Using USB camera:", usb_dev)
        return usb_dev

    # --- NO CAMERA ---
    print("[ERROR] No valid camera source available")
    return None

def start_viewer():
    global viewer, detector

    cam_input = build_camera_input(config.get("camera", {}))

    if cam_input is None:
        viewer = None
        print("[INFO] System started without camera. Waiting for user configuration.")
        return

    # stop existing viewer
    if viewer:
        viewer.running = False
        viewer.stop()
        time.sleep(0.5)

    viewer = VideoViewerPi(cam_input, "appsink",
                           resolution="640x480", fps="30")
    threading.Thread(target=viewer.start, daemon=True).start()

    if detector:
        detector.viewer = viewer
    else:
        globals()["detector"] = Detector(viewer, config)


# ============================================================
# START SYSTEM (CONFIG-DRIVEN)
# ============================================================
start_viewer()

# ============================================================
# STREAM VIDEO (MJPEG)
# ============================================================
@app.route("/stream")
def stream():
    def gen():
        while True:
            if not viewer:
                time.sleep(0.05)
                continue

            frame = viewer.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            h, w = frame.shape[:2]

            # Draw stored detection line
            line = config.get("line", [])
            if len(line) == 4:
                x1 = int(line[0] * w)
                y1 = int(line[1] * h)
                x2 = int(line[2] * w)
                y2 = int(line[3] * h)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

            ret, jpeg = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() +
                b"\r\n"
            )

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ============================================================
# CONFIG API (FOR UI)
# ============================================================
@app.route("/get_config")
def get_config():
    safe_cfg = config.copy()

    # Mask RTSP credentials
    if "camera" in safe_cfg and safe_cfg["camera"]["type"] == "rtsp":
        safe_cfg["camera"]["rtsp"]["username"] = "***"
        safe_cfg["camera"]["rtsp"]["password"] = "***"

    return jsonify(safe_cfg)

@app.route("/set_camera", methods=["POST"])
def set_camera():
    global config
    cam = request.json

    config["camera"] = cam
    save_config(config)

    start_viewer()
    return jsonify({"status": "Camera updated"})

# ============================================================
# SPRAYER IP
# ============================================================
@app.route("/set_esp_ip", methods=["POST"])
def set_esp_ip():
    global config
    data = request.json

    if "ip" not in data:
        return jsonify({"error": "Missing ip"}), 400

    config["esp32_ip"] = data["ip"]
    save_config(config)
    detector.update_config(config)

    return jsonify({"status": "ok", "ip": config["esp32_ip"]})

# ============================================================
# YOLO DATA
# ============================================================
@app.route("/yolo_data")
def yolo_data():
    return jsonify(detector.last_boxes)

# ============================================================
# LINE SAVE
# ============================================================
@app.route("/save_line", methods=["POST"])
def save_line():
    global config
    data = request.json

    config["line"] = data["line"]
    save_config(config)
    detector.update_config(config)

    return jsonify({"status": "ok"})

# ============================================================
# DETECTION CONTROL
# ============================================================
@app.route("/start_detection")
def start_detection():
    detector.start()
    return jsonify({"status": "Detecting"})

@app.route("/stop_detection")
def stop_detection():
    detector.stop()
    return jsonify({"status": "Stopped"})

# ============================================================
# MANUAL SPRAY
# ============================================================
@app.route("/spray_test")
def spray_test():
    detector.trigger_spray()
    return jsonify({"status": "Spray Triggered"})

# ============================================================
# MAIN UI
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
