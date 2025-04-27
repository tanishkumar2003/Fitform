# File: curl_detector.py

import cv2
import mediapipe as mp
import numpy as np
import logging
from session_tracker import ExerciseSession
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ——— Parameters ———
FLEXION_ANGLE_THRESHOLD   = 45   # degrees: angle at top of curl
EXTENSION_ANGLE_THRESHOLD = 170  # degrees: angle at bottom
ANGLE_TOLERANCE           = 15   # degrees tolerance for “OK” form
BICEP_VISIBILITY_THRESH   = 0.5  # landmark.visibility minimum

# Add new parameters for form tracking
SHOULDER_ELEVATION_THRESHOLD = 0.1  # Threshold for shoulder shrugging
ELBOW_FLARE_THRESHOLD = 15.0       # Degrees of acceptable elbow flare
TORSO_LEAN_THRESHOLD = 10.0        # Degrees of acceptable torso lean

# Global variables for tracking exercise state
counter = 0
stage = "down"
last_rep_time = None
rep_start_time = None  # Track individual rep timing
current_set_start_time = None
session_active = False
current_session = None

# ——— Setup MediaPipe Pose with better initialization ———
try:
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,  # Reduce to fastest model
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        smooth_landmarks=True  # Add smoothing
    )
    logger.info("MediaPipe Pose initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MediaPipe Pose: {e}")
    raise

# ——— Helper: calculate angle between three points ———
def calculate_angle(a, b, c):
    # Convert landmarks to numpy arrays if they're NormalizedLandmark objects
    if hasattr(a, 'x'):  # Check if input is a landmark
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
    
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

def calculate_shoulder_elevation(shoulder, hip):
    # Extract y coordinates directly
    return abs(shoulder.y - hip.y)

def calculate_elbow_flare(shoulder, elbow, wrist):
    # Use calculate_angle directly with landmarks
    return calculate_angle(shoulder, elbow, wrist)

def calculate_torso_lean(shoulder, hip):
    # Calculate angle directly from coordinates
    return abs(np.degrees(np.arctan2(shoulder.x - hip.x, shoulder.y - hip.y)))

def check_visibility(landmarks):
    missing_parts = []
    landmark_checks = [
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, "Left Shoulder"),
        (mp_pose.PoseLandmark.LEFT_ELBOW.value, "Left Elbow"),
        (mp_pose.PoseLandmark.LEFT_WRIST.value, "Left Wrist"),
        (mp_pose.PoseLandmark.LEFT_HIP.value, "Left Hip")
    ]
    
    for idx, name in landmark_checks:
        if landmarks[idx].visibility < BICEP_VISIBILITY_THRESH:
            missing_parts.append(name)
    
    return missing_parts

def end_set():
    """End current set and store final metrics."""
    global last_rep_time, rep_start_time, counter
    # Store final metrics if needed
    final_metrics = {
        'total_reps': counter,
        'last_angle': 0  # Default to 0 since latest_data is not defined
    }
    # Reset timing variables and counter
    last_rep_time = None
    rep_start_time = None
    counter = 0  # Reset counter when set ends
    logger.info(f"Set ended with {final_metrics['total_reps']} reps, timers and counter reset")
    return final_metrics

def init_session(session):
    global current_session, session_active, counter, current_set_start_time
    current_session = session
    session_active = True
    counter = 0
    current_set_start_time = time.time()
    logger.info("Session initialized")

def end_current_session():
    global current_session, session_active, counter, stage
    if current_session:
        current_session.save_session()
    current_session = None
    session_active = False
    counter = 0
    stage = "down"
    logger.info("Session ended")

# Add this new function to process single frames
def process_frame(frame):
    global counter, stage, current_session, last_rep_time, rep_start_time, session_active
    
    # Resize frame for faster processing
    frame = cv2.resize(frame, (640, 480))
    
    # Initialize default data structure
    default_metrics = {
        'shoulder_elevation': 0,
        'elbow_flare': 0,
        'torso_lean': 0,
        'rom_angle': 0,
        'rom_percentage': 0
    }
    
    data = {
        'reps': counter,
        'angle': 0,
        'feedback': "Press 'Start Session' to begin" if not session_active else "Initializing...",
        'form_metrics': default_metrics,
        'status': 'ok'
    }

    try:
        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)

        if not results or not results.pose_landmarks:
            data.update({
                'feedback': "No body detected - please step into frame",
                'status': 'no_detection',
                'missing_parts': []
            })
            cv2.putText(frame, data['feedback'],
                        (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
            return frame, data

        lm = results.pose_landmarks.landmark
        # Draw all landmarks & connections
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Check bicep/elbow landmark visibility
        elbow_landmark = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        if elbow_landmark.visibility < BICEP_VISIBILITY_THRESH:
            cv2.putText(frame, "Please bring your bicep into view",
                        (50,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,165,255), 2)
            data['feedback'] = "Please bring your bicep into view"
            return frame, data

        # Compute elbow angle (shoulder→elbow→wrist)
        shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        elbow    = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        wrist    = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]
        hip      = lm[mp_pose.PoseLandmark.LEFT_HIP.value]
        angle    = calculate_angle(shoulder, elbow, wrist)
        
        # Calculate form metrics
        shoulder_elevation = calculate_shoulder_elevation(shoulder, hip)
        elbow_flare = calculate_elbow_flare(shoulder, elbow, wrist)
        torso_lean = calculate_torso_lean(shoulder, hip)
        rom_percentage = (angle / EXTENSION_ANGLE_THRESHOLD) * 100
        
        # Update metrics with valid calculations
        form_metrics = {
            'shoulder_elevation': round(float(shoulder_elevation), 2),
            'elbow_flare': round(float(elbow_flare), 2),
            'torso_lean': round(float(torso_lean), 2),
            'rom_angle': round(float(angle), 2),
            'rom_percentage': round(float(rom_percentage), 2)
        }

        # Curl logic: detect rep up/down transitions
        # When arm straight (angle > extension threshold) → stage = "down"
        if angle > EXTENSION_ANGLE_THRESHOLD - ANGLE_TOLERANCE:
            stage = "down"
            if rep_start_time is None:
                rep_start_time = time.time()
        # When arm flexed (angle < flexion threshold) AND previously down → count a rep
        if session_active and stage == "down" and angle < FLEXION_ANGLE_THRESHOLD + ANGLE_TOLERANCE:
            stage   = "up"
            counter += 1
            current_time = time.time()
            
            # Calculate rep timing
            rep_duration = current_time - rep_start_time if rep_start_time else 0
            time_since_last = current_time - last_rep_time if last_rep_time else 0
            
            # Record detailed rep data
            if current_session:
                # Make sure rep data structure matches what session_tracker expects
                rep_data = {
                    "repNumber": counter,
                    "timestamp": current_time,
                    "metrics": {
                        "elbow_flare": form_metrics['elbow_flare'],
                        "torso_lean": form_metrics['torso_lean'],
                        "shoulder_elevation": form_metrics['shoulder_elevation'],
                        "rom_percentage": form_metrics['rom_percentage'],
                    },
                    "timing": {
                        "duration": rep_duration,
                        "time_since_last_rep": time_since_last,
                        "time_in_set": current_time - current_set_start_time if current_set_start_time else 0
                    }
                }
                current_session.add_rep_data(rep_data)
            
            last_rep_time = current_time
            rep_start_time = None  # Reset for next rep

        # End set if specific conditions are met (e.g., long pause)
        if last_rep_time and time.time() - last_rep_time > 10:  # Changed from 5 to 10 seconds
            if current_session and len(current_session.rep_data) > 0:
                current_session.end_set()
                current_session.start_set()
                last_rep_time = None

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

        # Enhanced form analysis with error checking
        form_issues = []
        try:
            lm = results.pose_landmarks.landmark
            shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            elbow = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            wrist = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]
            hip = lm[mp_pose.PoseLandmark.LEFT_HIP.value]

            missing_parts = check_visibility(lm)
    
            if missing_parts:
                msg = f"Please bring {', '.join(missing_parts)} into view"
                data.update({
                    'feedback': msg,
                    'status': 'low_visibility',
                    'missing_parts': missing_parts
                })
                cv2.putText(frame, msg, (50,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,165,255), 2)
                return frame, data

            # Calculate metrics with safety checks
            shoulder_elevation = calculate_shoulder_elevation(shoulder, hip)
            elbow_flare = calculate_elbow_flare(shoulder, elbow, wrist)
            torso_lean = calculate_torso_lean(shoulder, hip)
            
            # Update metrics only if valid calculations
            form_metrics = {
                'shoulder_elevation': round(float(shoulder_elevation), 2),
                'elbow_flare': round(float(elbow_flare), 2),
                'torso_lean': round(float(torso_lean), 2),
                'rom_angle': round(float(angle), 2) if 'angle' in locals() else 0
            }
            
            data['form_metrics'] = form_metrics
            
        except Exception as e:
            logger.error(f"Error in form analysis: {e}")
            data.update({
                'feedback': "Error analyzing form",
                'status': 'processing_error'
            })
            return frame, data

        # Update the data dictionary to include form metrics
        data = {
            'reps': counter,
            'angle': int(angle) if 'angle' in locals() else 0,
            'feedback': "; ".join(form_issues) if form_issues else form_msg,
            'form_metrics': form_metrics
        }
        
        # Visualize form issues on frame
        y_offset = 160
        for issue in form_issues:
            cv2.putText(frame, issue, (30, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 1)
            y_offset += 30

        # Overlay rep count and form feedback
        cv2.putText(frame, f"Reps: {counter}",
                    (30,40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
        cv2.putText(frame, f"Angle: {int(angle)} deg",
                    (30,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, form_msg,
                    (30,120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Instead of just returning frame, return a tuple with frame and data
        return frame, data

    except Exception as e:
        logger.error(f"Critical error in process_frame: {e}")
        data.update({
            'feedback': "Processing error - please try again",
            'status': 'critical_error',
            'reps': counter,
            'angle': 0,
            'form_metrics': {}
        })
        return frame, data

# Add cleanup on exit
def cleanup():
    global current_session
    if current_session:
        current_session.save_session()

import atexit
atexit.register(cleanup)

# Comment out or remove the original while loop when using as a module
if __name__ == '__main__':
    # Keep the original while loop for standalone usage
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, data = process_frame(frame)
        cv2.imshow("Curl Detector", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key stops
            break

    cap.release()
    cv2.destroyAllWindows()
    cleanup()
