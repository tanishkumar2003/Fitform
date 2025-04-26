# File: curl_detector.py

import cv2
import mediapipe as mp
import numpy as np

# ——— Parameters ———
FLEXION_ANGLE_THRESHOLD   = 45   # degrees: angle at top of curl
EXTENSION_ANGLE_THRESHOLD = 170  # degrees: angle at bottom
ANGLE_TOLERANCE           = 15   # degrees tolerance for “OK” form
BICEP_VISIBILITY_THRESH   = 0.5  # landmark.visibility minimum

# ——— Setup MediaPipe Pose ———
mp_pose    = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose       = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ——— Helper: calculate angle between three points ———
def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

# ——— Main loop ———
cap = cv2.VideoCapture(0)
counter = 0
stage   = None  # “up” or “down”

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip horizontally for mirror view
    frame = cv2.flip(frame, 1)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)

    # If no landmarks detected, prompt to adjust
    if not results.pose_landmarks:
        cv2.putText(frame, "No body detected – please step into frame.",
                    (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        cv2.imshow("Curl Detector", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break
        continue

    lm = results.pose_landmarks.landmark
    # Draw all landmarks & connections
    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # Check bicep/elbow landmark visibility
    elbow_landmark = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    if elbow_landmark.visibility < BICEP_VISIBILITY_THRESH:
        cv2.putText(frame, "Please bring your bicep into view",
                    (50,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,165,255), 2)
        cv2.imshow("Curl Detector", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    # Compute elbow angle (shoulder→elbow→wrist)
    shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    elbow    = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    wrist    = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]
    angle    = calculate_angle(shoulder, elbow, wrist)

    # Curl logic: detect rep up/down transitions
    # When arm straight (angle > extension threshold) → stage = "down"
    if angle > EXTENSION_ANGLE_THRESHOLD - ANGLE_TOLERANCE:
        stage = "down"
    # When arm flexed (angle < flexion threshold) AND previously down → count a rep
    if stage == "down" and angle < FLEXION_ANGLE_THRESHOLD + ANGLE_TOLERANCE:
        stage   = "up"
        counter += 1

    # Real-time form feedback
    if abs(angle - FLEXION_ANGLE_THRESHOLD) <= ANGLE_TOLERANCE:
        form_msg = "Full curl!"
        color = (0,255,0)
    elif abs(angle - EXTENSION_ANGLE_THRESHOLD) <= ANGLE_TOLERANCE:
        form_msg = "Arm fully extended!"
        color = (0,255,0)
    else:
        form_msg = "Maintain smooth curl form"
        color = (0,165,255)

    # Overlay rep count and form feedback
    cv2.putText(frame, f"Reps: {counter}",
                (30,40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
    cv2.putText(frame, f"Angle: {int(angle)} deg",
                (30,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    cv2.putText(frame, form_msg,
                (30,120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Curl Detector", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key stops
        break

cap.release()
cv2.destroyAllWindows()
