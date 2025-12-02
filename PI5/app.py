#!/usr/bin/env python3
from flask import Flask, render_template, Response, request, jsonify
import json, threading, time, cv2

from videoViewerPi2 import VideoViewerPi
from detection import Detector

CONFIG_PATH = "config.json"

app = Flask(__name__)

# --------------------------
# LOAD CONFIG
# --------------------------
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

# --------------------------
# START VIDEO CAPTURE
# --------------------------
viewer = VideoViewerPi("/dev/video0", "appsink", resolution="640x480", fps="30")
threading.Thread(target=viewer.start, daemon=True).start()

detector = Detector(viewer, config)


# --------------------------
# STREAM VIDEO (MJPEG)
# --------------------------
@app.route('/stream')
def stream():
    def gen():
        while True:
            frame = viewer.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            # get frame dimensions
            h, w = frame.shape[:2]

            # safely draw stored line if valid
            line = config.get("line", [])
            if len(line) == 4:
                x1 = int(line[0] * w)
                y1 = int(line[1] * h)
                x2 = int(line[2] * w)
                y2 = int(line[3] * h)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

            # encode jpeg
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() +
                b"\r\n"
            )

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


# --------------------------
# SAVE ESP32 IP
# --------------------------
@app.route("/set_esp_ip", methods=["POST"])
def set_esp_ip():
    global config
    data = request.json

    if "ip" not in data:
        return jsonify({"error": "Missing 'ip'"}), 400

    config["esp32_ip"] = data["ip"]
    save_config(config)
    detector.update_config(config)

    return jsonify({"status": "ok", "ip": config["esp32_ip"]})
    
# --------------------------
# YOLO DATA
# --------------------------
@app.route ("/yolo_data")
def yolo_data():
    return jsonify(detector.last_boxes)


# --------------------------
# SAVE LINE POSITION
# --------------------------
@app.route("/save_line", methods=["POST"])
def save_line():
    global config
    data = request.json

    config["line"] = data["line"]
    save_config(config)
    detector.update_config(config)

    return jsonify({"status": "ok"})


# --------------------------
# START / STOP DETECTION
# --------------------------
@app.route("/start_detection")
def start_detection():
    detector.start()
    return jsonify({"status": "Detecting"})

@app.route("/stop_detection")
def stop_detection():
    detector.stop()
    return jsonify({"status": "Stopped"})


# --------------------------
# MANUAL SPRAY
# --------------------------
@app.route("/spray_test")
def spray_test():
    detector.trigger_spray()
    return jsonify({"status": "Spray Triggered"})


# --------------------------
# MAIN UI
# --------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------------
# RUN SERVER
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
