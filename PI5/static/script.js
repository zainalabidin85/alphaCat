// ----------------------------------------
// CANVAS SETUP
// ----------------------------------------
let canvas = document.getElementById("videoCanvas");
let ctx = canvas.getContext("2d");

// Hidden MJPEG stream source
let img = document.getElementById("videoSource");

// YOLO boxes from backend
let yolo_boxes = [];

// Line drawing
let drawing = false;
let line = [];

// ----------------------------------------
// STATUS BAR
// ----------------------------------------
function showStatus(msg, color = "#28a745") {
    const bar = document.getElementById("statusBar");
    bar.style.background = color;
    bar.innerText = msg;
    bar.style.display = "block";

    setTimeout(() => {
        bar.style.display = "none";
    }, 3000);
}

// ----------------------------------------
// FETCH YOLO BOXES (ROBUST POLLING)
// ----------------------------------------
function fetchYOLO() {
    fetch("/yolo_data")
        .then(res => res.json())
        .then(data => {
            yolo_boxes = data;
        })
        .catch(() => {
            console.warn("YOLO fetch failed");
        })
        .finally(() => {
            setTimeout(fetchYOLO, 100); // 10 FPS
        });
}

fetchYOLO();

// ----------------------------------------
// DRAW LOOP (60 FPS)
// ----------------------------------------
function drawLoop() {

    // Wait until MJPEG frame is ready
    if (!img.complete || img.naturalWidth === 0) {
        requestAnimationFrame(drawLoop);
        return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // ----------------------------
    // Draw detection line
    // ----------------------------
    if (line.length === 4) {
        ctx.strokeStyle = "red";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(line[0] * canvas.width, line[1] * canvas.height);
        ctx.lineTo(line[2] * canvas.width, line[3] * canvas.height);
        ctx.stroke();
    }

    // ----------------------------
    // Draw YOLO boxes
    // ----------------------------
    let scaleX = canvas.width / img.naturalWidth;
    let scaleY = canvas.height / img.naturalHeight;

    yolo_boxes.forEach(b => {
        let x1 = b.x1 * scaleX;
        let y1 = b.y1 * scaleY;
        let x2 = b.x2 * scaleX;
        let y2 = b.y2 * scaleY;

        // Box
        ctx.strokeStyle = "lime";
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Label
        const label = `${b.cls} (${b.conf.toFixed(2)})`;
        ctx.font = "14px Arial";
        const textW = ctx.measureText(label).width;

        ctx.fillStyle = "rgba(0,255,0,0.7)";
        ctx.fillRect(x1, y1 - 18, textW + 8, 18);

        ctx.fillStyle = "black";
        ctx.fillText(label, x1 + 4, y1 - 4);
    });

    requestAnimationFrame(drawLoop);
}

drawLoop();

// ----------------------------------------
// LINE DRAWING (MOUSE EVENTS)
// ----------------------------------------
canvas.addEventListener("mousedown", e => {
    drawing = true;
    let r = canvas.getBoundingClientRect();
    line[0] = (e.clientX - r.left) / canvas.width;
    line[1] = (e.clientY - r.top) / canvas.height;
});

canvas.addEventListener("mouseup", e => {
    drawing = false;
    let r = canvas.getBoundingClientRect();
    line[2] = (e.clientX - r.left) / canvas.width;
    line[3] = (e.clientY - r.top) / canvas.height;
});

// ----------------------------------------
// SAVE ESP32 IP
// ----------------------------------------
function saveESPIP() {
    let ip = document.getElementById("esp_ip").value.trim();

    if (!ip) {
        alert("Please enter IP.");
        return;
    }

    fetch("/set_esp_ip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip })
    })
    .then(res => res.json())
    .then(data => {
        showStatus("ESP32 IP updated to: " + data.ip);
        if (typeof closePanel === "function") {
            closePanel();
        }
    })
    .catch(err => {
        alert("Failed to save ESP32 IP");
        console.error(err);
    });
}

// ----------------------------------------
// SAVE LINE
// ----------------------------------------
function saveLine() {
    fetch("/save_line", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ line })
    })
    .then(() => showStatus("Detection line saved"));
}

// ----------------------------------------
// DETECTION CONTROL
// ----------------------------------------
function startDetection() {
    fetch("/start_detection")
        .then(() => showStatus("Detection started"));
}

function stopDetection() {
    fetch("/stop_detection")
        .then(() => showStatus("Detection stopped", "#dc3545"));
}

function sprayTest() {
    fetch("/spray_test")
        .then(() => showStatus("Spray triggered!", "#17a2b8"));
}
