# File: app.py

import os
# Disable oneDNN custom ops to speed up TensorFlow/MediaPipe import
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import cv2
from flask import Flask, render_template, Response, json, request, jsonify, send_file
from curl_detector import process_frame, init_session, end_current_session
from session_tracker import ExerciseSession
import time
import atexit
import logging

last_set_metrics = {}
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize camera once
try:
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open camera")
    logger.info("Camera initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize camera: {e}")
    camera = None

# Ensure camera is released on shutdown
@atexit.register
def cleanup():
    global camera
    if camera is not None:
        camera.release()
        logger.info("Camera released")

# Shared container for the latest metrics
latest_data = {}

# Add frame rate control
FRAME_RATE = 30
SKIP_FRAMES = 2  # Process every nth frame for metrics
frame_count = 0

# Add global variables for session management
current_session = None
session_active = False

# Add session state tracking
SESSION_STATES = {
    'INACTIVE': 0,
    'SESSION_STARTED': 1,
    'SET_IN_PROGRESS': 2,
    'SET_COMPLETED': 3,
    'FEEDBACK_REQUIRED': 4
}

current_state = SESSION_STATES['INACTIVE']

def validate_state_transition(expected_state, next_state, operation):
    """Validate if the requested operation is allowed in current state"""
    global current_state
    if current_state != expected_state:
        raise ValueError(f"Invalid operation: {operation}. Must complete previous steps first.")
    current_state = next_state
    return True

def generate_frames():
    """Yields MJPEG frames for /video_feed, and updates latest_data."""
    global latest_data, frame_count
    last_time = time.time()
    
    while True:
        current_time = time.time()
        # Control frame rate
        if (current_time - last_time) < 1.0/FRAME_RATE:
            continue
            
        last_time = current_time
        
        if camera is None or not camera.isOpened():
            logger.error("Camera not available in generate_frames")
            time.sleep(0.1)
            continue

        success, frame = camera.read()
        if not success or frame is None:
            logger.error("Failed to read frame")
            time.sleep(0.1)
            continue

        # Only process every nth frame for metrics
        if frame_count % SKIP_FRAMES == 0:
            processed_frame, data = process_frame(frame)
            latest_data = data
        else:
            # Just flip and resize the frame without processing
            frame = cv2.flip(cv2.resize(frame, (640, 480)), 1)
            processed_frame = frame

        frame_count += 1

        # JPEG-encode with lower quality for faster transmission
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def generate_metrics():
    """Server-Sent Events stream of the latest_data for /metrics."""
    last_time = time.time()
    
    while True:
        current_time = time.time()
        # Limit metrics update rate
        if (current_time - last_time) < 0.1:  # 10 updates per second max
            time.sleep(0.01)
            continue
            
        last_time = current_time
        if latest_data:
            yield f"data: {json.dumps(latest_data)}\n\n"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/metrics')
def metrics():
    return Response(
        generate_metrics(),
        mimetype='text/event-stream'
    )

@app.route('/start_session', methods=['POST'])
def start_session():
    global current_session, session_active, current_state
    try:
        if current_session is not None:
            raise ValueError("Session already in progress. End current session first.")
            
        validate_state_transition(SESSION_STATES['INACTIVE'], 
                                SESSION_STATES['SESSION_STARTED'], 
                                'start_session')
        
        weight = request.json.get('weight', 0)
        # Remove weight validation to allow 0
            
        user_context = request.json.get('userContext', {
            "goal": "Technique Improvement",
            "experienceLevel": "Beginner",
            "notes": None
        })
        equipment = {
            "type": "Dumbbells",
            "weight": float(weight),
            "unit": "lbs"
        }
        
        current_session = ExerciseSession(user_context=user_context, equipment=equipment)
        init_session(current_session)
        session_active = True
        logger.info(f"Session started with weight: {weight}lbs")
        
        return jsonify({
            "status": "success", 
            "state": "session_started",
            "message": f"Session started with {weight}lbs"
        })
    except (ValueError, TypeError) as ve:
        current_state = SESSION_STATES['INACTIVE']
        current_session = None
        session_active = False
        logger.error(f"Validation error in start_session: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        current_state = SESSION_STATES['INACTIVE']
        current_session = None
        session_active = False
        logger.error(f"Error starting session: {e}")
        return jsonify({"status": "error", "message": f"Failed to start session: {str(e)}"}), 500

@app.route('/start_set', methods=['POST'])
def start_set():
    """Start a new set within the current session."""
    try:
        validate_state_transition(SESSION_STATES['SESSION_STARTED'], 
                                SESSION_STATES['SET_IN_PROGRESS'], 
                                'start_set')
        
        if current_session:
            current_session.start_set()
            return jsonify({"status": "success", "message": "Set started successfully"})
        return jsonify({"status": "error", "message": "No active session"}), 400
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error starting set: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/end_set', methods=['POST'])
def end_set():
    global current_state
    try:
        if current_state != SESSION_STATES['SET_IN_PROGRESS']:
            raise ValueError("No active set to end")
        if not current_session:
            raise ValueError("No active session found")
        
        # Import the end_set function from curl_detector
        from curl_detector import end_set as detector_end_set
        
        # Call the end_set function from curl_detector to reset counters
        final_metrics = detector_end_set()
        
        # Calculate aggregate metrics for the set
        if hasattr(current_session, 'rep_data') and current_session.rep_data:
            set_metrics = current_session._calculate_set_metrics()
        else:
            set_metrics = {}
            
        # Update state
        current_state = SESSION_STATES['FEEDBACK_REQUIRED']
        global last_set_metrics
        last_set_metrics = set_metrics
        
        return jsonify({
            "status": "success",
            "message": "Set ended. Please provide feedback.",
            "state": "feedback_required",
            "metrics": set_metrics,  # Send aggregate metrics
            "total_reps": final_metrics.get('total_reps', 0)
        })
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error ending set: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_set_feedback', methods=['POST'])
def submit_set_feedback():
    global current_state, latest_data
    try:
        if current_state != SESSION_STATES['FEEDBACK_REQUIRED']:
            raise ValueError("Cannot submit feedback - no set ended")
            
        if not request.is_json:
            raise ValueError("Feedback must be provided")
            
        # Extract feedback from request
        feedback = {
            "rpe": request.json.get('rpe'),
            "rir": request.json.get('rir'),
            "fatiguePointReason": request.json.get('fatigueReason'),
            "muscleFeelFocus": request.json.get('muscleFocus', "Biceps"),
            "painFlag": request.json.get('painFlag', False),
            "painLocation": request.json.get('painLocation'),
            "notes": request.json.get('notes'),
            "metrics": last_set_metrics # Add metrics if available
        }
        
        # Validate required fields
        if feedback['rpe'] is None or feedback['rir'] is None:
            raise ValueError("RPE and RIR are required feedback fields")
            
        if current_session:
            current_session.end_set(subjective_feedback=feedback)
            current_state = SESSION_STATES['SESSION_STARTED']
            logger.info(f"Set feedback recorded successfully: RPE={feedback['rpe']}, RIR={feedback['rir']}")
            
            return jsonify({
                "status": "success",
                "message": "Feedback recorded successfully"
            })
            
        raise ValueError("No active session found")
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update_session_notes', methods=['POST'])
def update_session_notes():
    try:
        if current_session and request.is_json:
            notes = request.json.get('notes')
            current_session.update_notes(notes)
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "No active session"}), 400
    except Exception as e:
        logger.error(f"Error updating notes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/end_session', methods=['POST'])
def end_session():
    global current_state
    try:
        if current_state == SESSION_STATES['FEEDBACK_REQUIRED']:
            raise ValueError("Please submit set feedback before ending session")
            
        if current_session:
            summary = request.json if request.is_json else {}
            current_session.add_session_summary(summary)
            filename = current_session.save_session()
            end_current_session()
            current_state = SESSION_STATES['INACTIVE']
            return jsonify({
                "status": "success", 
                "filename": filename,
                "message": "Session saved successfully"
            })
        return jsonify({"status": "error", "message": "No active session"}), 400
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download_session/<filename>')
def download_session(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Set camera properties for better performance
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, FRAME_RATE)
    
    # Disable Flask's auto-reloader to avoid double initialization
    app.run(debug=True, use_reloader=False, threaded=True)
