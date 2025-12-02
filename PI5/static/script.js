// ----------------------------------------
// CANVAS SETUP
// ----------------------------------------
let canvas = document.getElementById("videoCanvas");
let ctx = canvas.getContext("2d");

// The hidden video stream source
let img = document.getElementById("videoSource");

// YOLO boxes from backend
let yolo_boxes = [];

// Line drawing (user-defined)
let drawing = false;
let line = [];

// ----------------------------------------
// SHOWING STATUS
//-----------------------------------------
function showStatus(msg,color = "#28a745"){
    const bar = document.getElementById("statusBar");
    bar.style.background = color;
    bar.innerText = msg;
    bar.style.display = "block";
    
    setTimeout(() => {
        bar.style.display = "none";
    }, 3000);
}
// ----------------------------------------
// FETCH YOLO BOXES (poll /yolo_data)
// ----------------------------------------
function fetchYOLO() {
    fetch("/yolo_data")
        .then(res => res.json())
        .then(data => {
            yolo_boxes = data; // array of {cls, conf, x1, y1, x2, y2}
        });

    setTimeout(fetchYOLO, 100);  // 10 FPS polling
}

fetchYOLO();


// ----------------------------------------
// DRAW LOOP (60 FPS)
// ----------------------------------------
function drawLoop() {
    // Draw live video
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // ----------------------------
    // Draw detection line
    // ----------------------------
    if (line.length === 4) {
        ctx.strokeStyle = "red";
        ctx.lineWidth = 3;

        ctx.beginPath();
        ctx.moveTo(line[0] * canvas.width,  line[1] * canvas.height);
        ctx.lineTo(line[2] * canvas.width,  line[3] * canvas.height);
        ctx.stroke();
    }

    // ----------------------------
    // Draw YOLO boxes
    // ----------------------------
    yolo_boxes.forEach(b => {
        // Scale boxes from absolute pixels to canvas size
        let scaleX = canvas.width  / img.naturalWidth;
        let scaleY = canvas.height / img.naturalHeight;

        let x1 = b.x1 * scaleX;
        let y1 = b.y1 * scaleY;
        let x2 = b.x2 * scaleX;
        let y2 = b.y2 * scaleY;

        // Draw box
        ctx.strokeStyle = "lime";
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw label
        let label = `${b.cls} (${b.conf.toFixed(2)})`;
        ctx.fillStyle = "rgba(0,255,0,0.7)";
        ctx.fillRect(x1, y1 - 20, ctx.measureText(label).width + 10, 20);

        ctx.fillStyle = "black";
        ctx.font = "16px Arial";
        ctx.fillText(label, x1 + 5, y1 - 5);
    });

    requestAnimationFrame(drawLoop);
}

drawLoop();


// ----------------------------------------
// MOUSE EVENTS FOR LINE DRAWING
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
    let ip = document.getElementById("esp_ip").value;

    if (!ip) {
        alert("Please enter IP.");
        return;
    }

    fetch("/set_esp_ip", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ ip: ip })
    })
    .then(res => res.json())
    .then(data => showStatus("ESP32 IP updated to: " + data.ip));
}


// ----------------------------------------
// SAVE LINE
// ----------------------------------------
function saveLine() {
    fetch("/save_line", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ line: line })
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
    
function stopDetection()  { 
    fetch("/stop_detection")
    .then(() => showStatus("Detection stopped", "#dc3545"));
     }
     
function sprayTest()      { 
    fetch("/spray_test")
    .then(() => showStatus("Spray triggered!", "#17a2b8")); }
