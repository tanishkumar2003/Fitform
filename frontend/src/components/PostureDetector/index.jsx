import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './PostureDetector.css';  // We'll create this next

const MjpegViewer = React.memo(({ src, style, alt }) => (
  <img src={src} alt={alt} style={style} />
));

const initialMetrics = {
  reps: 0,
  angle: 0,
  feedback: 'Waiting to start…',
  form_metrics: {
    shoulder_elevation: 0,
    elbow_flare: 0,
    torso_lean: 0,
    rom_percentage: 0,
  }
};

export default function PostureDetector() {
  const [userId, setUserId] = useState('');
  const [weight, setWeight] = useState(0);
  const [sessionActive, setSessionActive] = useState(false);
  const [metrics, setMetrics] = useState(initialMetrics);
  const [currentSet, setCurrentSet] = useState(1);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedback, setFeedback] = useState({
    rpe: '',
    rir: '',
    fatigueReason: 'target_reps_met',
    muscleFocus: 'Biceps',
    painFlag: false,
    painLocation: '',
    notes: ''
  });

  // Buttons state
  const [buttonsState, setButtonsState] = useState({
    startSession: false,
    startSet: true,
    endSet: true,
    endSession: true
  });

  const clearOldSession = async () => {
    try {
      await axios.post('/cv/end_session');
    } catch (err) {
      // ignore errors
    }
  };

  const startSession = async () => {
    if (!userId.trim()) return alert('Please enter a User ID');
    if (isNaN(weight)) return alert('Please enter a valid weight');

    await clearOldSession();
    try {
      await axios.post('/cv/start_session', {
        weight: parseFloat(weight),
        userContext: {
          user_id: userId.trim(),
          goal: "Technique Improvement",
          experienceLevel: "Beginner"
        }
      });
      setSessionActive(true);
      setButtonsState({
        startSession: true,
        startSet: false,
        endSet: true,
        endSession: false
      });
    } catch (err) {
      console.error(err);
      alert('Error starting session');
    }
  };

  const startSet = async () => {
    try {
      await axios.post('/cv/start_set');
      setButtonsState(prev => ({
        ...prev,
        startSet: true,
        endSet: false
      }));
    } catch (err) {
      console.error(err);
      alert('Error starting set');
    }
  };

  const endSet = async () => {
    try {
      const res = await axios.post('/cv/end_set');
      if (res.data.status === 'success') {
        setShowFeedbackForm(true);
        setButtonsState(prev => ({
          ...prev,
          endSet: true
        }));
      }
    } catch (err) {
      console.error(err);
      alert('Error ending set');
    }
  };

  const submitSetFeedback = async () => {
    if (isNaN(feedback.rpe) || isNaN(feedback.rir)) {
      return alert('Please provide both RPE and RIR');
    }

    try {
      const res = await axios.post('/cv/submit_set_feedback', feedback);
      if (res.data.status === 'success') {
        setCurrentSet(prev => prev + 1);
        setShowFeedbackForm(false);
        setFeedback({
          rpe: '',
          rir: '',
          fatigueReason: 'target_reps_met',
          muscleFocus: 'Biceps',
          painFlag: false,
          painLocation: '',
          notes: ''
        });
        setButtonsState(prev => ({
          ...prev,
          startSet: false,
          endSet: true
        }));
      }
    } catch (err) {
      console.error(err);
      alert('Error submitting feedback');
    }
  };

  const endSession = async () => {
    if (showFeedbackForm) {
      return alert('Please submit set feedback before ending session');
    }

    try {
      const finalFeedback = {
        overallFeeling: prompt('Rate your overall session (1-5):', '5'),
        notes: prompt('Any final notes about the session?', ''),
        totalSets: currentSet - 1
      };

      const res = await axios.post('/cv/end_session', finalFeedback);
      if (res.data.status === 'success') {
        setSessionActive(false);
        setCurrentSet(1);
        setButtonsState({
          startSession: false,
          startSet: true,
          endSet: true,
          endSession: true
        });
        setMetrics(initialMetrics);

        if (res.data.filename) {
          window.location.href = `/cv/download_session/${res.data.filename}`;
        }
      }
    } catch (err) {
      console.error(err);
      alert('Error ending session');
    }
  };

  useEffect(() => {
    if (!sessionActive) return;

    const es = new EventSource('/cv/metrics');
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMetrics(data);
      } catch (err) {
        console.error('Error processing metrics:', err);
      }
    };

    return () => es.close();
  }, [sessionActive]);

  return (
    <div className="container">
      <h1>Bicep Curl Form Detector</h1>
      
      <div className="session-status">
        {sessionActive ? 'Session Active' : 'No Active Session'}
      </div>

      {/* Session Setup */}
      <div className="session-controls">
        <div className="weight-input">
          <label>
            Weight (lbs):
            <input
              type="number"
              value={weight}
              onChange={e => setWeight(e.target.value)}
              min="0"
              step="0.5"
              disabled={sessionActive}
            />
          </label>
        </div>

        {!sessionActive && (
          <div className="user-input">
            <label>
              User ID:
              <input
                type="text"
                value={userId}
                onChange={e => setUserId(e.target.value)}
                placeholder="e.g. user_1"
              />
            </label>
          </div>
        )}

        <div className="button-group">
          <button 
            onClick={startSession} 
            disabled={buttonsState.startSession}
            className="control-btn"
          >
            Start Session
          </button>
          <button 
            onClick={startSet} 
            disabled={buttonsState.startSet}
            className="control-btn"
          >
            Start Set
          </button>
          <button 
            onClick={endSet} 
            disabled={buttonsState.endSet}
            className="control-btn"
          >
            End Set
          </button>
          <button 
            onClick={endSession} 
            disabled={buttonsState.endSession}
            className="control-btn"
          >
            End Session
          </button>
        </div>
      </div>

      {/* Video Feed */}
      {sessionActive && (
        <div className="video-container">
          <MjpegViewer
            src="/cv/video_feed"
            alt="Live video feed"
            style={{ width: '100%', borderRadius: '10px' }}
          />
        </div>
      )}

      {/* Metrics Display */}
      <div className="stats">
        <div>Set: {currentSet}</div>
        <div>Reps: {metrics.reps}</div>
        <div>Angle: {metrics.angle}°</div>
        <div>Form: {metrics.feedback}</div>
      </div>

      {/* Form Metrics */}
      <div className="form-metrics">
        <h3>Detailed Form Metrics</h3>
        <div className="metrics-grid">
          <div>Shoulder Elevation: {metrics.form_metrics.shoulder_elevation}</div>
          <div>Elbow Flare: {metrics.form_metrics.elbow_flare}°</div>
          <div>Torso Lean: {metrics.form_metrics.torso_lean}°</div>
          <div>ROM %: {metrics.form_metrics.rom_percentage}%</div>
        </div>
      </div>

      {/* Feedback Form */}
      {showFeedbackForm && (
        <div className="feedback-form">
          <h3>Set Feedback</h3>
          
          <div className="form-group">
            <label>Rate of Perceived Exertion (1-10):</label>
            <input
              type="number"
              min="1"
              max="10"
              step="0.5"
              value={feedback.rpe}
              onChange={e => setFeedback(prev => ({ ...prev, rpe: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label>Reps in Reserve:</label>
            <input
              type="number"
              min="0"
              max="10"
              value={feedback.rir}
              onChange={e => setFeedback(prev => ({ ...prev, rir: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label>Fatigue Point Reason:</label>
            <select 
              value={feedback.fatigueReason}
              onChange={e => setFeedback(prev => ({ ...prev, fatigueReason: e.target.value }))}
            >
              <option value="target_reps_met">Target Reps Met</option>
              <option value="muscular_failure">Muscular Failure</option>
              <option value="form_breakdown">Form Breakdown</option>
              <option value="pain">Pain/Discomfort</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label>Primary Muscle Feel:</label>
            <select
              value={feedback.muscleFocus}
              onChange={e => setFeedback(prev => ({ ...prev, muscleFocus: e.target.value }))}
            >
              <option value="Biceps">Biceps</option>
              <option value="Forearms">Forearms</option>
              <option value="Shoulders">Shoulders</option>
              <option value="Back">Back</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={feedback.painFlag}
                onChange={e => setFeedback(prev => ({ ...prev, painFlag: e.target.checked }))}
              />
              Experienced Pain/Discomfort
            </label>
            {feedback.painFlag && (
              <input
                type="text"
                placeholder="Location of pain"
                value={feedback.painLocation}
                onChange={e => setFeedback(prev => ({ ...prev, painLocation: e.target.value }))}
              />
            )}
          </div>

          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={feedback.notes}
              onChange={e => setFeedback(prev => ({ ...prev, notes: e.target.value }))}
            />
          </div>

          <button onClick={submitSetFeedback} className="control-btn">
            Submit Set Feedback
          </button>
        </div>
      )}

      {/* Instructions */}
      <div className="instructions">
        <h2>Instructions:</h2>
        <ul>
          <li>Enter your User ID and the weight you'll be using</li>
          <li>Click "Start Session" to begin</li>
          <li>Stand in view of the camera</li>
          <li>Perform bicep curls with your left arm</li>
          <li>Click "End Set" after completing your set</li>
          <li>Provide feedback about your set</li>
          <li>Click "End Session" when finished</li>
        </ul>
      </div>
    </div>
  );
}