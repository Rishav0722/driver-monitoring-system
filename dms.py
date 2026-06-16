import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import os
import urllib.request
import requests
import winsound
import threading

def beep():
    winsound.Beep(1000, 500)  # Beep sound for alert

def save_alert(ear):
    requests.post("http://127.0.0.1:8000/alerts", params={"ear": ear})

# Download model if needed
model_path = 'face_landmarker.task'
if not os.path.exists(model_path):
    print("Downloading face landmarker model...")
    urllib.request.urlretrieve(
        'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
        model_path
    )

# EAR calculation
def calculate_ear(landmarks, eye_indices, image_w, image_h, frame):
    points = []
    for i in eye_indices:
        x = int(landmarks[i].x * image_w)
        y = int(landmarks[i].y * image_h)
        points.append((x, y))

# draw small circle on each eye landmark
    for point in points:
        cv2.circle(frame, point, 2, (255, 255, 0), -1)

    # vertical distances
    A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    # horizontal distance
    C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))

    ear = (A + B) / (2.0 * C)
    return ear

# Eye landmark indices for MediaPipe
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

EAR_THRESHOLD = 0.25
CLOSED_FRAMES  = 20

closed_counter = 0
alert_playing = False

# Setup detector
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    output_facial_transformation_matrixes=True
)
detector = vision.FaceLandmarker.create_from_options(options)

# Start video capture with some delay(2)
cap = cv2.VideoCapture(0)
time.sleep(2)
print("DMS Running... Press Q to quit.")

#confirm frames are read
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue

#convert to RGB and process with MediaPipe
    h, w = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    result = detector.detect(mp_image)

    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
        matrix = result.facial_transformation_matrixes[0]

        left_ear  = calculate_ear(landmarks, LEFT_EYE,  w, h, frame)
        right_ear = calculate_ear(landmarks, RIGHT_EYE, w, h, frame)
        avg_ear   = (left_ear + right_ear) / 2.0

        # Display EAR on screen
        cv2.putText(frame, f'EAR: {avg_ear:.2f}', (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2)

# check if EAR is below threshold and count consecutive frames to avoid false positives
        if avg_ear < EAR_THRESHOLD:
            closed_counter += 1
        else:
            closed_counter = 0
        if closed_counter >= CLOSED_FRAMES:
            cv2.putText(frame, 'DROWSY ALERT!', (30, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            if alert_playing == False:
                print("DROWSY ALERT!")
                threading.Thread(target=save_alert, args=(round(avg_ear, 2),), daemon=True).start()
                # Start beep in a separate thread to avoid blocking the main loop
                threading.Thread(target=beep, daemon=True).start()      
                alert_playing = True
        else:
            alert_playing = False

    cv2.imshow('DMS', frame)    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()