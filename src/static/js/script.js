// static/js/script.js
function toggleMode() {
    var element = document.body;
    element.classList.toggle("night");

    var button = document.getElementById("mode-toggle");
    button.classList.toggle("night-mode");  // Toggle the night-mode class on the button

    if (button.classList.contains("night-mode")) {
        button.innerHTML = "Night Mode 🌜"; // Change to Night mode text
    } else {
        button.innerHTML = "Day Mode 🌞"; // Change to Day mode text
    }
}

const video = document.getElementById('video');
const recordButton = document.getElementById('recordButton');
let isRecording = false;
let stream = null;
let mediaRecorder = null;

// Function to initialize the camera
async function initCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        video.srcObject = stream;
        video.play();
        mediaRecorder = new MediaRecorder(stream);
        handleRecordingSetup();
        console.log("Camera and microphone are active.");
    } catch (error) {
        console.error("Error accessing the camera and microphone:", error);
    }
}

// Function to handle recording setup
function handleRecordingSetup() {
    const recordedChunks = [];

    mediaRecorder.ondataavailable = function(e) {
        if (e.data.size > 0) recordedChunks.push(e.data);
    };

    mediaRecorder.onstop = function() {
        const blob = new Blob(recordedChunks, {
            type: "video/webm"
        });
        const url = URL.createObjectURL(blob);
        // Here you can handle the blob further, e.g., save it or send it to a server
        console.log("Recording stopped and data prepared.");
    };
}

// Toggle recording and streaming
recordButton.addEventListener('click', function() {
    if (!stream) {
        initCamera();
        recordButton.textContent = 'Pause'; // Change to pause icon/text
        isRecording = true;
    } else if (isRecording) {
        mediaRecorder.stop();
        stream.getTracks().forEach(track => track.stop()); // Stops the camera
        stream = null;
        recordButton.textContent = 'Start'; // Change back to the start icon/text
        isRecording = false;
        console.log("Camera and microphone are turned off.");
    } else {
        initCamera();
        mediaRecorder.start();
        recordButton.textContent = 'Pause'; // Change to pause icon/text
        isRecording = true;
    }
});
