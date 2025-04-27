// frontend/src/components/PostureDetector/index.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../../index.css';

// Keep the MJPEG <img> stable across updates
const MjpegViewer = React.memo(({ src, style, alt }) => (
  <img src={src} alt={alt} style={style} />
));

const initialMetrics = {
  reps: 0,
  angle: 0,
  feedback: 'Waiting to start…',
  form_metrics: {
    shoulder_elevation: 0,
    elbow_flare:        0,
    torso_lean:         0,
    rom_percentage:     0,
  }
};

export default function PostureDetector() {
  const [userId, setUserId]             = useState('');
  const [sessionActive, setSessionActive] = useState(false);
  const [metrics, setMetrics]           = useState(initialMetrics);

  // Force‐end any stale session on the server
  const clearOldSession = async () => {
    try {
      await axios.post('/cv/end_session', {});
    } catch {
      // ignore errors
    }
  };

  // Start detection flow
  const startDetection = async () => {
    if (!userId.trim()) return alert('Please enter a User ID');
    await clearOldSession();
    try {
      await axios.post('/cv/start_session', {
        userContext: { user_id: userId.trim() }
      });
      setMetrics(initialMetrics);
      setSessionActive(true);
    } catch (err) {
      console.error(err);
      alert('Error starting posture detector');
    }
  };

  // End detection flow
  const endDetection = async () => {
    try {
      await axios.post('/cv/end_session', {});
    } catch {
      // ignore
    }
    // Reload the page—resets UI and server state
    window.location.reload();
  };

  // Subscribe to SSE metrics once active
  useEffect(() => {
    if (!sessionActive) return;
    const es = new EventSource('/cv/metrics');
    es.onmessage = e => {
      try {
        setMetrics(JSON.parse(e.data));
      } catch (err) {
        console.error('SSE parse error', err);
      }
    };
    return () => es.close();
  }, [sessionActive]);

  // Safely pull metrics
  const fm = metrics.form_metrics || {};
  const shoulder = fm.shoulder_elevation  ?? 0;
  const elbow    = fm.elbow_flare         ?? 0;
  const torso    = fm.torso_lean          ?? 0;
  const romPct   = fm.rom_percentage      ?? 0;

  return (
    <div className="container">
      <h1>Bicep Curl Detector</h1>

      {!sessionActive ? (
        <div className="card">
          <div className="input-group">
            <label>User ID:</label>
            <input
              type="text"
              value={userId}
              onChange={e => setUserId(e.target.value)}
              placeholder="e.g. user_1"
            />
          </div>
          <button className="btn btn-primary" onClick={startDetection}>
            Start Detection
          </button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <MjpegViewer
            src="/cv/video_feed"
            alt="Live video feed"
            style={{
              width: '100%',
              display: 'block',
              borderTopLeftRadius: 'var(--radius)',
              borderTopRightRadius: 'var(--radius)'
            }}
          />
          <div style={{ padding: '1.5rem' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '1.5rem',
              fontSize: '1.1rem'
            }}>
              <span><strong>Reps:</strong> {metrics.reps}</span>
              <span style={{ textAlign: 'right' }}>
                <strong>Angle:</strong> {metrics.angle}°
              </span>
            </div>

            <div style={{ marginBottom: '1.5rem', fontSize: '1rem' }}>
              <strong>Feedback:</strong> {metrics.feedback}
            </div>

            <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>
              Form Metrics
            </h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              fontSize: '0.95rem'
            }}>
              <div>Shoulder Elevation: {shoulder.toFixed(2)}</div>
              <div>Elbow Flare: {elbow.toFixed(2)}°</div>
              <div>Torso Lean: {torso.toFixed(2)}°</div>
              <div>ROM %: {romPct.toFixed(1)}%</div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button className="btn btn-secondary" onClick={endDetection}>
                End Session
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
