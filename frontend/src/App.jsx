// src/App.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import Router from './router';
import './index.css';

export default function App() {
  return (
    <>
      <header className="header">
        <div className="brand">
          <img src="/logo.png" alt="FitForm.ai Logo" className="logo" />
          <span className="brand-name">fitform.ai</span>
        </div>
        <nav>
          <Link to="/workout">Workout Logger</Link>
          <Link to="/posture">Posture Detector</Link>
        </nav>
      </header>

      <main className="container">
        <div className="card">
          <Router />
        </div>
      </main>
    </>
  );
}
