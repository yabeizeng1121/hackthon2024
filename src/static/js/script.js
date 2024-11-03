// static/js / script.js
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

// Recording functionality
const video = document.getElementById('video');
const controlButton = document.getElementById('controlButton');
let isRecording = false;
let sessionTime = 0;
let recordingTimer = null;
let emotionFetchInterval = null;


document.addEventListener('DOMContentLoaded', function () {
    if (controlButton) {
        controlButton.addEventListener('click', toggleRecording);
        console.log('Event listener added to control button');
    }
});

function toggleRecording() {
    console.log('Toggle recording called'); // Debug log
    setLoadingState(true);

    $.post('/toggle_recording', function (response) {
        if (response.error) {
            alert('Error: ' + response.error);
            isRecording = false;
            updateControlButton();
            setLoadingState(false);
            return;
        }

        isRecording = response.recording;
        updateControlButton();

        if (isRecording) {
            // Start recording timer and emotion fetch interval
            startRecordingTimer();
            startEmotionFetchInterval();
            console.log('Recording started');
        } else {
            // Stop recording timer and emotion fetch interval
            stopRecordingTimer();
            stopEmotionFetchInterval();
            console.log('Recording stopped');
        }
        setLoadingState(false);
    })
        .fail(function (xhr, status, error) {
            console.error('Error toggling recording:', error);
            alert('Failed to toggle recording. Please try again.');
            isRecording = false;
            updateControlButton();
            setLoadingState(false);
        });
}

function startEmotionFetchInterval() {
    if (!emotionFetchInterval) {
        emotionFetchInterval = setInterval(fetchDominantEmotion, 5000);
    }
}

function stopEmotionFetchInterval() {
    if (emotionFetchInterval) {
        clearInterval(emotionFetchInterval);
        emotionFetchInterval = null;
    }
}

function updateControlButton() {
    if (isRecording) {
        controlButton.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
        controlButton.classList.add('recording');
    } else {
        controlButton.innerHTML = '<i class="fas fa-video"></i><span>Start Recording</span>';
        controlButton.classList.remove('recording');
    }
}

function setLoadingState(loading) {
    controlButton.disabled = loading;
    if (loading) {
        controlButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Initializing...</span>';
    } else {
        updateControlButton();
    }
}

function startRecordingTimer() {
    sessionTime = 0;
    updateTimer();
    recordingTimer = setInterval(updateTimer, 1000);
}

function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
    sessionTime = 0;
    updateTimer();
}

function updateTimer() {
    const minutes = Math.floor(sessionTime / 60);
    const seconds = sessionTime % 60;
    const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    const timerElement = document.getElementById('recordingTimer');
    if (timerElement) {
        timerElement.textContent = timeString;
    }

    const sessionTimeElement = document.getElementById('sessionTime');
    if (sessionTimeElement) {
        sessionTimeElement.textContent = timeString;
    }

    sessionTime++;
}

function fetchDominantEmotion() {
    $.get('/dominant_emotion', function (response) {
        console.log(response);
        $('#dominantEmotion').text(response.dominant_emotion);
        document.getElementById('emotionAdvice').innerHTML = response.suggestion;
        console.log(response.dominant_emotion);
    })
        .fail(function (error) {
            console.error("Error fetching dominant emotion:", error);
        });
}

document.addEventListener('keydown', function (e) {
    if (e.code === 'Space' &&
        !['input', 'textarea'].includes(document.activeElement.tagName.toLowerCase())) {
        e.preventDefault();
        toggleRecording();
    }
});

console.log('Script loaded');