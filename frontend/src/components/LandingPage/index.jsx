import React from 'react';
import { Link } from 'react-router-dom';
import './styles.css';

export default function LandingPage() {
  return (
    <div className="landing-container">
      <section className="hero">
        <h1 className="hero-title">
          Train Smarter with
          <span className="gradient-text"> AI-Powered</span> Form Analysis
        </h1>
        <p className="hero-subtitle">
          Real-time feedback, personalized insights, and smart tracking for perfect form every rep
        </p>
        <div className="cta-buttons">
          <Link to="/workout" className="btn btn-primary">Start Workout</Link>
          <Link to="/posture" className="btn btn-secondary">Try Form Detection</Link>
        </div>
      </section>

      <section className="features">
        <div className="feature-card">
          <div className="feature-icon">🎯</div>
          <h3>Real-Time Form Analysis</h3>
          <p>Get instant feedback on your exercise form using advanced computer vision</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Smart Progress Tracking</h3>
          <p>Track your improvements with detailed metrics and performance insights</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">🤖</div>
          <h3>AI Workout Advice</h3>
          <p>Receive personalized recommendations based on your performance data</p>
        </div>
      </section>

      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h4>Start a Session</h4>
            <p>Choose your exercise and weight</p>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <h4>Perform Your Sets</h4>
            <p>Get real-time feedback on your form</p>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <h4>Track Progress</h4>
            <p>Review your performance and improvements</p>
          </div>
        </div>
      </section>
    </div>
  );
}