// src/router.jsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import WorkoutLogger from './components/WorkoutLogger';
import PostureDetector from './components/PostureDetector';

export default function Router() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/workout" replace />} />
      <Route path="/workout" element={<WorkoutLogger />} />
      <Route path="/posture" element={<PostureDetector />} />
    </Routes>
  );
}
  