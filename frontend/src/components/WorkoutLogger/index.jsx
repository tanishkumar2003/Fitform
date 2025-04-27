// src/components/WorkoutLogger/index.jsx
import React, { useState } from 'react';
import axios from 'axios';
import '../../index.css';            // ensure we load the updated styles

console.log('✅ WorkoutLogger loaded');

export default function WorkoutLogger() {
  // state hooks
  const [userId, setUserId]           = useState('');
  const [workouts, setWorkouts]       = useState([]);
  const [isLogging, setIsLogging]     = useState(false);
  const [submitting, setSubmitting]   = useState(false);
  const [advice, setAdvice]           = useState('');
  const [loadingAdvice, setLoadingAdvice] = useState(false);

  // workout form handlers (unchanged)
  function addWorkout() {
    setWorkouts(ws => [...ws, { name: '', sets: [{ reps: '', weight: '' }] }]);
  }
  function removeWorkout(i) {
    setWorkouts(ws => ws.filter((_, idx) => idx !== i));
  }
  function addSet(i) {
    setWorkouts(ws =>
      ws.map((w, idx) =>
        idx === i ? { ...w, sets: [...w.sets, { reps: '', weight: '' }] } : w
      )
    );
  }
  function removeSet(i, j) {
    setWorkouts(ws =>
      ws.map((w, idx) =>
        idx === i
          ? { ...w, sets: w.sets.filter((_, sj) => sj !== j) }
          : w
      )
    );
  }
  function updateField(i, j, field, value) {
    setWorkouts(ws =>
      ws.map((w, idx) => {
        if (idx !== i) return w;
        if (j === null) {
          return { ...w, name: value };
        } else {
          const newSets = w.sets.map((s, sj) =>
            sj === j ? { ...s, [field]: value } : s
          );
          return { ...w, sets: newSets };
        }
      })
    );
  }

  // submit new session
  async function handleSubmit(e) {
    e.preventDefault();
    if (!userId.trim()) return alert('User ID is required');
    if (workouts.length === 0) return alert('Add at least one workout');
    setSubmitting(true);
    try {
      await axios.post('/api/sessions', {
        user_id: userId.trim(),
        workouts
      });
      alert('Session saved!');
      setIsLogging(false);
      setWorkouts([]);
    } catch (err) {
      console.error(err);
      alert('Error saving session');
    } finally {
      setSubmitting(false);
    }
  }

  // fetch AI advice
  async function handleGetAdvice() {
    if (!userId.trim()) return alert('Enter a User ID');
    setLoadingAdvice(true);
    try {
      const res = await axios.get(
        `/api/advice/${encodeURIComponent(userId.trim())}?limit=5`
      );
      setAdvice(res.data.advice);
    } catch (err) {
      console.error(err);
      alert('Error fetching advice');
    } finally {
      setLoadingAdvice(false);
    }
  }

  // ── Initial “Start / Advice” screen ─────────────────
  if (!isLogging) {
    return (
      <div className="container">
        <h1>Workout Logger</h1>
        <div className="input-group">
          <label>User ID:</label>
          <input
            type="text"
            value={userId}
            onChange={e => setUserId(e.target.value)}
            placeholder="e.g. user_1"
          />
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={() => {
              if (!userId.trim()) return alert('Enter a User ID');
              setIsLogging(true);
              addWorkout();
            }}
          >
            Start New Session
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleGetAdvice}
            disabled={loadingAdvice}
          >
            {loadingAdvice ? 'Loading…' : 'Get Personalized Advice'}
          </button>
        </div>

        {advice && (
          <div className="advice-box">
            <h2>AI Advice</h2>
            <p>{advice}</p>
          </div>
        )}
      </div>
    );
  }

  // ── Dynamic “New Session” form ────────────────────────
  return (
    <div className="container">
      <h1>New Workout Session</h1>
      <form onSubmit={handleSubmit}>
        {workouts.map((w, i) => (
          <div
            key={i}
            style={{
              marginBottom: '1.5rem',
              padding: '1rem',
              border: '1px solid #e1e1e1',
              borderRadius: '6px',
              background: '#fafafa',
            }}
          >
            <div className="input-group">
              <label>Exercise:</label>
              <input
                type="text"
                value={w.name}
                onChange={e => updateField(i, null, 'name', e.target.value)}
                placeholder="Bench Press"
                required
              />
              <button
                type="button"
                className="btn"
                onClick={() => removeWorkout(i)}
                style={{ background: 'transparent', color: '#999' }}
              >
                ✕
              </button>
            </div>

            {w.sets.map((s, j) => (
              <div key={j} className="input-group">
                <input
                  type="number"
                  value={s.reps}
                  onChange={e => updateField(i, j, 'reps', e.target.value)}
                  placeholder="Reps"
                  required
                  style={{ maxWidth: '80px' }}
                />
                <input
                  type="number"
                  value={s.weight}
                  onChange={e => updateField(i, j, 'weight', e.target.value)}
                  placeholder="Weight (lbs)"
                  required
                  style={{ maxWidth: '100px' }}
                />
                <button
                  type="button"
                  className="btn"
                  onClick={() => removeSet(i, j)}
                  style={{ background: 'transparent', color: '#999' }}
                >
                  ✕
                </button>
              </div>
            ))}

            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => addSet(i)}
            >
              + Add Set
            </button>
          </div>
        ))}

        <button
          type="button"
          className="btn btn-primary"
          onClick={addWorkout}
          style={{ marginRight: '0.75rem' }}
        >
          + Add Workout
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving…' : 'Save Session'}
        </button>
      </form>
    </div>
  );
}
