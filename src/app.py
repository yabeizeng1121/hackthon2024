from flask import Flask, render_template, Response, jsonify
import cv2
from deepface import DeepFace
import threading
import time
import atexit
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

# set up your OpenAI API key
# define system prompt for OpenAI API
SYSTEM_PROMPT = "You are helping individuals who don't know how to read emotions and respond to them."
client = OpenAI(
    api_key=os.getenv("OPENAI_KEY"),
)
# define video input
VIDEO_INPUT = os.getenv("VIDEO_INPUT")

app = Flask(__name__)

# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = None
is_recording = False
frame_count = 0
emotion_cache = None
emotion_average = []
dominant_emotion_result = None


@app.route("/toggle_recording", methods=["POST"])
def toggle_recording():
    """toggle recordings for video input"""
    global is_recording, cap
    is_recording = not is_recording

    if is_recording:
        # initialize camera when starting recording
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        cap = cv2.VideoCapture(VIDEO_INPUT)
        if not cap.isOpened():
            is_recording = False
            return jsonify({"recording": False, "error": "Failed to open camera"})
    else:
        # Release camera when stopping recording
        if cap is not None:
            cap.release()
            cap = None

    return jsonify({"recording": is_recording})


def analyze_emotion(face_roi):
    """Perform emotion analysis in a separate thread to avoid blocking frame generation."""
    global emotion_cache, emotion_average
    try:
        result = DeepFace.analyze(
            face_roi, actions=["emotion"], enforce_detection=False
        )
        emotion_cache = result[0]["dominant_emotion"]
        # Grab emotions
        emotion_average.append(result[0]["emotion"])
    except Exception as e:
        print(f"Emotion analysis error: {str(e)}")
        emotion_cache = "Error"


def calculate_dominant_emotion():
    """Helper function to calculate the dominant emotion from emotion_average."""
    global emotion_average, dominant_emotion_result

    if not emotion_average:
        return None

    emotion_totals = {}
    for emotions in emotion_average:
        for emotion, score in emotions.items():
            emotion_totals[emotion] = emotion_totals.get(emotion, 0) + score

    emotion_averages = {
        emotion: total / len(emotion_average)
        for emotion, total in emotion_totals.items()
    }
    dominant_emotion = max(emotion_averages, key=emotion_averages.get)
    dominant_emotion_result = dominant_emotion

    # Clear emotion average to avoid redundant calculations
    emotion_average.clear()
    return dominant_emotion_result


def generate_frames():
    """generate frames with the emption"""
    global is_recording, cap, frame_count, emotion_cache

    while True:
        if not is_recording or cap is None:
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + b"\r\n")
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success:
            break

        try:
            frame = cv2.resize(frame, (640, 480))
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray_frame, scaleFactor=1.2, minNeighbors=7, minSize=(30, 30)
            )

            for x, y, w, h in faces:
                face_roi = frame[y : y + h, x : x + w]

                if frame_count % 10 == 0:
                    emotion_thread = threading.Thread(
                        target=analyze_emotion, args=(face_roi,)
                    )
                    emotion_thread.start()

                emotion = emotion_cache if emotion_cache else "Analyzing..."
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    emotion,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2,
                )

            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

            frame_count += 1

            if frame_count % 300 == 0:
                calculate_dominant_emotion()

        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            if cap is not None:
                cap.release()
                cap = None
            is_recording = False
            break


def generate_emotion_suggestion(emotion):
    """Uses OpenAI's API to generate a response suggestion for a given emotion."""
    user_prompt = (
        f"Emotion: {emotion}\n\n"
        "1 - I will feed in an emotion that an individual with autism sees in a one-on-one setting or in a group setting.\n"
        "2 - Provide one suggestion on how an individual with autism can appropriately respond to this emotion.\n"
        "3 - Give only the suggestion, without repeating the emotion, and ensure it is actionable.\n"
        "4 - Limit the action response to 15 words and the language response to 30 words.\n"
        "5 - Make sure the suggestions prioritize the comfort of individuals with Alexithymia.\n"
        "6 - Format your suggestion as follows, using HTML:\n\n"
        "Using the following format:\n"
        "<p><strong>Action:</strong> <em>What they should do</em></p>\n"
        "<p><strong>Language:</strong> <em>What they should say</em></p>"
    )

    try:
        # Generate response from OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract the generated suggestion from the response
        suggestion = response.choices[0].message.content
        return suggestion
    except Exception as e:
        print(f"Error generating suggestion: {e}")
        return "Unable to generate suggestion at this time."


@app.route("/dominant_emotion", methods=["GET"])
def get_dominant_emotion():
    """Endpoint to return the last calculated dominant emotion."""
    if dominant_emotion_result:
        suggestion = generate_emotion_suggestion(dominant_emotion_result)
        return jsonify(
            {
                "dominant_emotion": dominant_emotion_result,
                "suggestion": suggestion,
            }
        )
    else:
        return jsonify({"dominant_emotion": "Waiting...", "suggestion": "Waiting..."})


@app.route("/")
def index():
    """entrypoint"""
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """shows video feed"""
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def cleanup():
    """clean up"""
    global cap
    if cap is not None:
        cap.release()


atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", default=8080))
