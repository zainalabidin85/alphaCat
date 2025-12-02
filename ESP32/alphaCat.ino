/****************************************************
 * alphaCat @ ESP32 = Web File Manager + Motor/Servo/Relay
 * Supports Arduino IDE 2.x (no plugin SPIFF needed)
 * alphaCat.ino flash normally via Arduino IDE
 * data files uploaded via browser visit http://<ESP-IP>/upload
 ****************************************************/

#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <Preferences.h>
#include <ESP32Servo.h>
#include "driver/ledc.h"
#include <LiquidCrystal_I2C.h>

/****************************************************
 * LCD
 ****************************************************/
LiquidCrystal_I2C lcd(0x27, 16, 2);

/****************************************************
 * USER CONFIG
 ****************************************************/
#define AP_SSID        "alphaCat-setup"
#define AP_PASSWORD    "12345678"
#define RESET_PIN      14

#define RELAY_PIN 15
#define MOTOR_PWM 25
#define MOTOR_DIR1 26
#define MOTOR_DIR2 27
#define SERVO_PIN 13

Preferences prefs;
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

Servo myServo;

int motorSpeed = 0;
String motorState = "Stopped";
bool relayState = false;
int servoAngle = 90;

String savedSSID, savedPASS;
bool wifiConnected = false;


/****************************************************
 * PWM: LEDC Core 3.x
 ****************************************************/
void updatePWM() {
    int duty = (motorState == "Forward" || motorState == "Reverse")
               ? (motorSpeed * 255) / 100
               : 0;

    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

/****************************************************
 * WebSocket Notify
 ****************************************************/
void notifyClients() {
    StaticJsonDocument<200> doc;
    doc["motorSpeed"] = motorSpeed;
    doc["motorState"] = motorState;
    doc["relayState"] = relayState;
    doc["servoAngle"] = servoAngle;

    String json;
    serializeJson(doc, json);
    ws.textAll(json);
}

/****************************************************
 * WebSocket Events
 ****************************************************/
void onWebSocketEvent(AsyncWebSocket *server,
                      AsyncWebSocketClient *client,
                      AwsEventType type,
                      void *arg,
                      uint8_t *data,
                      size_t len) 
{
    if (type == WS_EVT_CONNECT) {
        notifyClients();
    }
    else if (type == WS_EVT_DATA) {
        StaticJsonDocument<200> doc;
        deserializeJson(doc, data, len);

        if (doc.containsKey("motorState")) {
            motorState = doc["motorState"].as<String>();

            if (motorState == "Forward") {
                digitalWrite(MOTOR_DIR1, HIGH);
                digitalWrite(MOTOR_DIR2, LOW);
            } else if (motorState == "Reverse") {
                digitalWrite(MOTOR_DIR1, LOW);
                digitalWrite(MOTOR_DIR2, HIGH);
            } else {
                digitalWrite(MOTOR_DIR1, LOW);
                digitalWrite(MOTOR_DIR2, LOW);
            }
            updatePWM();
        }

        if (doc.containsKey("motorSpeed")) {
            motorSpeed = constrain(doc["motorSpeed"].as<int>(), 0, 100);
            updatePWM();
        }

        if (doc.containsKey("relayState")) {
            relayState = doc["relayState"];
            digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
        }

        if (doc.containsKey("servoAngle")) {
            servoAngle = constrain(doc["servoAngle"].as<int>(), 0, 180);
            myServo.write(servoAngle);
        }

        notifyClients();
    }
}

/****************************************************
 * Reset WiFi Button
 ****************************************************/
void checkResetButton() {
    static unsigned long startPress = 0;

    if (digitalRead(RESET_PIN) == LOW) {
        if (startPress == 0) startPress = millis();

        lcd.setCursor(0, 1);
        lcd.print("Hold RESET...   ");

        if (millis() - startPress > 5000) {
            prefs.begin("wifi", false);
            prefs.clear();
            prefs.end();

            lcd.clear();
            lcd.print("WiFi Reset...");
            delay(500);
            ESP.restart();
        }
    } 
    else startPress = 0;
}

/****************************************************
 * WiFi AP Mode
 ****************************************************/
void startAPMode() {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);

    IPAddress ip = WiFi.softAPIP();

    Serial.println("[AP] Access Point Mode Started");
    Serial.print("[AP] SSID: ");
    Serial.println(AP_SSID);
    Serial.print("[AP] IP Address: ");
    Serial.println(ip);    

    lcd.clear();
    lcd.print("AP Mode Ready");
    lcd.setCursor(0, 1);
    lcd.print(ip.toString());

    wifiConnected = false;
}

/****************************************************
 * Try WiFi Connect
 ****************************************************/
bool tryConnectWiFi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSSID.c_str(), savedPASS.c_str());

    lcd.clear();
    lcd.print("Connecting WiFi");

    for (int i = 0; i < 20; i++) {
        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("\n[WiFi] Connected");
            Serial.print("[WiFi] IP Address: ");
            Serial.println(WiFi.localIP());

            lcd.clear();
            lcd.print("WiFi Connected");
            lcd.setCursor(0, 1);
            lcd.print(WiFi.localIP().toString());
            return true;
        }
        delay(500);
    }
    return false;
}

/****************************************************
 * Save WiFi Credentials
 ****************************************************/
void handleWiFiSave(AsyncWebServerRequest *req) {
    if (!req->hasParam("ssid", true) ||
        !req->hasParam("pass", true)) 
    {
        req->send(400, "text/plain", "Missing SSID or PASS");
        return;
    }

    prefs.begin("wifi", false);
    prefs.putString("ssid", req->getParam("ssid", true)->value());
    prefs.putString("pass", req->getParam("pass", true)->value());
    prefs.end();

    req->send(200, "text/plain", "Saved. Rebooting...");
    delay(600);
    ESP.restart();
}

/****************************************************
 * FILE UPLOAD HANDLER
 ****************************************************/
void handleFileUpload(
    AsyncWebServerRequest *request,
    String filename,
    size_t index,
    uint8_t *data,
    size_t len,
    bool final)
{
    if (!index) {
        if (!filename.startsWith("/")) filename = "/" + filename;
        request->_tempFile = SPIFFS.open(filename, "w");
    }
    request->_tempFile.write(data, len);
    if (final) {
        request->_tempFile.close();
        request->send(200, "text/plain", "File uploaded!");
    }
}

/****************************************************
 * FILE MANAGER: LIST FILES
 ****************************************************/
String listFilesHTML() {
    String html = "<h2>SPIFFS File Manager</h2><ul>";
    File root = SPIFFS.open("/");
    File file = root.openNextFile();

    while (file) {
        String name = file.name();
        html += "<li>" + name +
                " (<a href='" + name + "'>open</a>)" +
                " <a href='/delete?file=" + name + "'>[delete]</a></li>";
        file = root.openNextFile();
    }

    html += "</ul><hr>";
    html += "<form method='POST' action='/upload' enctype='multipart/form-data'>";
    html += "<input type='file' name='data'><input type='submit' value='Upload'>";
    html += "</form>";

    return html;
}

/****************************************************
 * Setup API Routes
 ****************************************************/
void setupAPI() {

    /******** Root UI ********/
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *req){
        if (wifiConnected)
            req->send(SPIFFS, "/index_2.html", "text/html");
        else
            req->send(SPIFFS, "/index_1.html", "text/html");
    });

    /******** WiFi Save ********/
    server.on("/savewifi", HTTP_POST, handleWiFiSave);

    /******** Motor ********/
    server.on("/motor/forward", HTTP_GET, [](AsyncWebServerRequest *req){
        motorState = "Forward";
        digitalWrite(MOTOR_DIR1, HIGH);
        digitalWrite(MOTOR_DIR2, LOW);
        updatePWM();
        notifyClients();
        req->send(200, "text/plain", "Forward");
    });

    server.on("/motor/reverse", HTTP_GET, [](AsyncWebServerRequest *req){
        motorState = "Reverse";
        digitalWrite(MOTOR_DIR1, LOW);
        digitalWrite(MOTOR_DIR2, HIGH);
        updatePWM();
        notifyClients();
        req->send(200, "text/plain", "Reverse");
    });

    server.on("/motor/off", HTTP_GET, [](AsyncWebServerRequest *req){
        motorState = "Stopped";
        digitalWrite(MOTOR_DIR1, LOW);
        digitalWrite(MOTOR_DIR2, LOW);
        updatePWM();
        notifyClients();
        req->send(200, "text/plain", "Stopped");
    });

    server.on("/motor/speed", HTTP_GET, [](AsyncWebServerRequest *req){
        if (req->hasParam("value")) {
            motorSpeed = constrain(req->getParam("value")->value().toInt(), 0, 100);
            updatePWM();
            notifyClients();
            req->send(200, "text/plain", "Speed updated");
        } else req->send(400, "text/plain", "Missing value");
    });

    /******** Relay ********/
    server.on("/relay/on", HTTP_GET, [](AsyncWebServerRequest *req){
        relayState = true;
        digitalWrite(RELAY_PIN, HIGH);
        notifyClients();
        req->send(200, "text/plain", "Relay ON");
    });

    server.on("/relay/off", HTTP_GET, [](AsyncWebServerRequest *req){
        relayState = false;
        digitalWrite(RELAY_PIN, LOW);
        notifyClients();
        req->send(200, "text/plain", "Relay OFF");
    });

    /******** Servo ********/
    server.on("/servo", HTTP_GET, [](AsyncWebServerRequest *req){
        if (req->hasParam("angle")) {
            servoAngle = constrain(req->getParam("angle")->value().toInt(), 0, 180);
            myServo.write(servoAngle);
            notifyClients();
            req->send(200, "text/plain", "Servo updated");
        } 
        else req->send(400, "text/plain", "Missing angle");
    });

    /****************************************************
     * FILE MANAGER ROUTES
     ****************************************************/
    server.on("/upload", HTTP_GET, [](AsyncWebServerRequest *req){
        req->send(200, "text/html", listFilesHTML());
    });

    server.on("/upload", HTTP_POST,
        [](AsyncWebServerRequest *req){},
        handleFileUpload
    );

    server.on("/delete", HTTP_GET, [](AsyncWebServerRequest *req){
        if (req->hasParam("file")) {
            String path = req->getParam("file")->value();
            SPIFFS.remove(path);
            req->send(200, "text/html", listFilesHTML());
        }
        else req->send(400, "text/plain", "Missing file parameter");
    });

}

/****************************************************
 * SETUP
 ****************************************************/
void setup() {
    Serial.begin(115200);

    lcd.init();
    lcd.backlight();
    lcd.print("alphaCat v3");

    pinMode(RESET_PIN, INPUT_PULLUP);
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(MOTOR_DIR1, OUTPUT);
    pinMode(MOTOR_DIR2, OUTPUT);

    /******** SPIFFS ********/
    SPIFFS.begin(true);

    /******** Load WiFi ********/
    prefs.begin("wifi", true);
    savedSSID = prefs.getString("ssid", "");
    savedPASS = prefs.getString("pass", "");
    prefs.end();

    /******** LEDC PWM ********/
    ledc_timer_config_t tcfg = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 5000,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&tcfg);

    ledc_channel_config_t ccfg = {
        .gpio_num   = MOTOR_PWM,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LEDC_CHANNEL_0,
        .timer_sel  = LEDC_TIMER_0,
        .duty       = 0,
        .hpoint     = 0,
        .flags      = {}
    };
    ledc_channel_config(&ccfg);

    /******** Servo ********/
    myServo.attach(SERVO_PIN);
    myServo.write(servoAngle);

    /******** WiFi ********/
    if (savedSSID == "") startAPMode();
    else {
        wifiConnected = tryConnectWiFi();
        if (!wifiConnected) startAPMode();
    }

    /******** Webserver ********/
    ws.onEvent(onWebSocketEvent);
    server.addHandler(&ws);
    setupAPI();
    server.begin();
}

/****************************************************
 * LOOP
 ****************************************************/
void loop() {
    ws.cleanupClients();
    checkResetButton();
}
