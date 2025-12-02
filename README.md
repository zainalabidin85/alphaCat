# 📘 **alphaCat – Raspberry Pi Vision System (YOLO + ESP32 Sprayer)**  
### **Smart Animal Detection & Water Spray Automation – Agriculture Engineering UniMAP**


---

## 📌 **Overview**

**alphaCat** is a Raspberry-Pi–based real-time vision system that:

✔ Streams video from RTSP/USB/CSI cameras  
✔ Runs **YOLO11** object detection  
✔ Allows the user to draw a detection line  
✔ Triggers an **ESP32-based sprayer** when a cat or person crosses the line  
✔ Displays live video + bounding boxes + line overlay in a web UI  
✔ Supports high-performance **appsink** pipeline for real-time inference  

Built for agricultural automation projects (UniMAP Agriculture Engineering) — especially for detecting cat intrusion in farms.

---

# 📂 **Project Structure**

```
alphaCat/
│── videoViewerPi2.py
│── app.py
│── detection.py
│── config.json
│── static/
│     └── script.js
│── templates/
│     └── index.html
│── yolo11n.pt
```

---

# 🚀 Installation

### System packages
```
sudo apt update  
sudo apt install -y python3-pip python3-opencv git \
    gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    gstreamer1.0-rtsp
```
### Python dependencies
```
pip3 install ultralytics flask numpy requests
```
---

# 🎥 Running

To run the alphaCat, reside to the approriate folder, then;
```
python3 app.py
```
Access dashboard at:  
```
http://<raspberry-pi-ip>:5000
```
---

# 🧠 YOLO Detection Logic

YOLO runs inside detection.py and checks if a detected object intersects the user‑drawn line.

Spray triggers if:  
• object center touches the line   
• cooldown passed  

---

# 🔌 ESP32 Sprayer Integration

Connect ESP32 Sprayer in UI Controls by typing down the ip address (once)

ESP32 will expose websocket:  
- /relay/on  - Switch on the relay
- /relay/off - Switch off the relay

Sprayer activation is done via simple HTTP GET.

---

# 🖥 UI Controls

| Button | Function |
|--------|----------|
| Save IP | Saves ESP32 sprayer IP |
| Save Line | Saves detection line |
| Start Detection | Runs YOLO |
| Stop Detection | Stops YOLO |
| Spray Test | Activates sprayer |

---

# 🔧 API Endpoints

- POST /set_esp_ip  
- POST /save_line  
- GET /start_detection  
- GET /stop_detection  
- GET /spray_test 
- GET /yolo_data  - UI thread

---

# 🚀 Performance Tips

- Use YOLO11n  
- Ensure Pi is cooled  

---

# 🧪 More class to trigger by ESP32 Sprayer

- Modify the config.json file to add more yolo object
- Example;
  
```
{
  "esp32_ip": "192.168.1.88",
  "line": [0.1, 0.5, 0.9, 0.5],
  "detect_objects": ["cat","person","bird"]
}
```
- This additional class to trigger sprayer must be further modifiying in the detection.py file
- Find this function update_target_objects(self) and modify as follows:
- Example;
  
```
    def update_target_objects(self):
        lst = self.config.get("detect_objects", ["cat","person","bird"])
        self.target_objects = set(lst)
```
Note: Please be make sure that the object classes in yolo are the same as your class string 

---

# 📄 License

MIT License  
