
# alphaCat — ESP32 Smart Sprayer System  

A fully web-controlled agriculture automation module with ESP32, including:

- Real-time control for **motor**, **relay**, and **servo**
- **LCD display** (I2C 16×2)
- **WiFi AP/STA mode switching**
- **Automatic WiFi credential reset button**
- **Web UI loading from SPIFFS**
- **Built-in Web File Manager** (upload HTML/JS/Images without any Arduino plugin)
- **WebSocket streaming** for instant browser feedback
- **Full compatibility with Arduino IDE 2.x**

This project is designed for **agriculture engineering**, precision spraying, IoT-enabled robotics, research, and prototyping.

---

# ⭐ Features

### 🔹 1. Web-Based Dashboard
The ESP32 hosts a modern dashboard that lets you control:

- Motor (Forward / Reverse / Stop)
- Motor PWM Speed (0–100%)
- Servo Angle (0–180°)
- Relay ON/OFF (for sprayer pump)
- Draw detection lines (if used with external AI system)

HTML/JS files are served from SPIFFS.

---

### 🔹 2. Integrated Web File Manager  
Upload UI files without plugins:

```
http://<esp32-ip>/upload
```

Allows:

- Upload `.html`, `.js`, `.css`, `.png`, `.jpg`, etc.
- Delete any file
- Browse SPIFFS content
- **Works on Arduino IDE 2.x.x**  
- No need for "ESP32 Sketch Data Upload" plugin

---

### 🔹 3. WiFi Modes (AP & STA)

#### AP Mode  
If no WiFi credentials are saved, ESP32 starts its own hotspot:

| SSID | Password |
|------|----------|
| alphaCat-setup | 12345678 |

Default AP IP:

```
192.168.4.1
```

#### Station Mode  
If saved WiFi credentials exist, ESP32 connects automatically and prints:

```
[WiFi] Connected!
[WiFi] IP Address: 192.168.x.x
```

LCD also displays IP.

---

### 🔹 4. WiFi Reset Button (GPIO 14)
Holding the reset button for **5 seconds**:

- Clears saved WiFi credentials (ESP32 Preferences)
- Restarts ESP32
- Boots back into AP mode  
- Safe to short GPIO14 → GND when pressed

---

### 🔹 5. Motor Control (PWM)
- Uses ESP32 Core 3.x LEDC API  
- PWM pin: **GPIO 25**  
- Direction pins: **GPIO 26 & 27**

---

### 🔹 6. Real-time WebSocket Status
Browser instantly receives updates when:

- Motor state changes  
- Speed changes  
- Relay toggles  
- Servo moves  

---

### 🔹 7. LCD Status Display
Displays:

- Boot status  
- WiFi mode  
- Assigned IP  
- Reset conditions  

---

# ⭐ Hardware Requirements

### ✔ ESP32 DevKit / WROOM  
### ✔ LCD 16×2 I2C (0x27)  
### ✔ Motor driver (H-bridge / BTS7960 / L298n, etc.)  
### ✔ Sprayer pump (triggered via relay)  
### ✔ Servo motor for directional spray  
### ✔ Pushbutton for WiFi reset  
### ✔ Power supply (5V or appropriate motor power)

---

# ⭐ Pinout Diagram

| Function | GPIO |
|---------|------|
| LCD SDA | 21 |
| LCD SCL | 22 |
| Motor PWM | 25 |
| Motor DIR1 | 26 |
| Motor DIR2 | 27 |
| Relay | 15 |
| Servo | 13 |
| Reset Button | 14 → GND |

---

# ⭐ Installation Instructions (Arduino IDE 2.x)

### 1️⃣ Install Board Package  
Add ESP32 boards:

```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

Install:

**ESP32 Arduino Core 3.x.x** (recommended 3.3.4)

---

### 2️⃣ Install Required Libraries

| Library | Source |
|---------|--------|
| ESPAsyncWebServer | https://github.com/me-no-dev/ESPAsyncWebServer |
| AsyncTCP | https://github.com/me-no-dev/AsyncTCP |
| LiquidCrystal_I2C | Arduino Library Manager |
| ESP32Servo | Arduino Library Manager |
| ArduinoJson | Arduino Library Manager |

---

### 3️⃣ Compile & Upload

Open **alphaCat.ino**, then:

```
Upload → Normal sketch upload
```

ESP32 reboots and displays IP on Serial + LCD.

---

### 4️⃣ Upload Web Files (HTML/JS/CSS)

Open browser:

```
http://<esp32-ip>/upload
```

Upload:

- index_1.html  
- index_2.html  
 

No plugin required.

---

# ⭐ Web File Manager Endpoints

| URL | Function |
|---------|---------|
| `/upload` | Upload files, browse SPIFFS |
| `/delete?file=/name` | Delete file |
| `/` | Load main UI based on WiFi mode |

---

# ⭐ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/motor/forward` | GET | Motor forward |
| `/motor/reverse` | GET | Motor reverse |
| `/motor/off` | GET | Motor stop |
| `/motor/speed?value=N` | GET | Set PWM speed |
| `/relay/on` | GET | Relay ON |
| `/relay/off` | GET | Relay OFF |
| `/servo?angle=N` | GET | Move servo |
| `/savewifi` | POST | Save SSID + PASS |
| `/upload` | POST | Upload file |
| `/delete` | GET | Delete file |

---

# ⭐ WebSocket Messages

Browser receives JSON:

```json
{
  "motorSpeed": 80,
  "motorState": "Forward",
  "relayState": true,
  "servoAngle": 45
}
```

Browser sends:

```json
{
  "motorSpeed": 50
}
```

---

# ⭐ Reset Button Behavior

Pressing GPIO14 → GND for **>5 seconds**:

- Clears WiFi credentials (`Preferences`)
- Displays "WiFi Reset"
- Reboots and starts AP mode

---

# ⭐ Project Architecture

```
alphaCat
├── alphaCat.ino
├── /SPIFFS (uploaded via browser)
│   ├── index_1.html
│   ├── index_2.html
```

---

# ⭐ Troubleshooting

### 💬 UI not loading CSS/JS  
Cause: missing files  
Fix: upload via `/upload`

### 💬 “Handler did not handle request”  
Cause: SPIFFS empty  
Fix: upload HTML/JS

### 💬 LCD not working  
Fix: check I2C address (0x27)

### 💬 Reset button not working  
Fix: ensure GPIO14 → GND  
Configured as `INPUT_PULLUP`

---

# ⭐ Future Improvements

- Add password protection to `/upload`
- Add OTA firmware uploader  
- Add drag & drop multi-file upload
- Add auto-format SPIFFS button  
- Add dark/light mode UI  
- Add buzzer for reset countdown  
- Add JSON configuration file in SPIFFS

---

# ⭐ License

MIT License

---

# ⭐ Maintainer

**Zainal Abidin Arsat**  
UniMAP — Agricultural Engineering  
alphaCat Smart Agriculture Project
