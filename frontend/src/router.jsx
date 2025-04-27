import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import WorkoutLogger from './components/WorkoutLogger';
import PostureDetector from './components/PostureDetector';

export default function Router() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/workout" element={<WorkoutLogger />} />
      <Route path="/posture" element={<PostureDetector />} />
    </Routes>
  );
}