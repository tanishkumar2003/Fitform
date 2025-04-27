from flask import Flask, render_template, Response, json
import cv2
from curl_detector import process_frame
import time

app = Flask(__name__)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Process frame using existing curl detector logic
        processed_frame, data = process_frame(frame)
        
        # Convert to bytes for streaming
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_metrics():
    while True:
        success, frame = camera.read()
        if success:
            _, data = process_frame(frame)
            yield f"data: {json.dumps(data)}\n\n"
        time.sleep(0.1)  # Add small delay to prevent overwhelming the browser

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/metrics')
def metrics():
    return Response(generate_metrics(), 
                   mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
