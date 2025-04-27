# File: app/services/advice_service.py

import os
from typing import List
from datetime import datetime
from app.database import db
from app.config import settings
from google import genai

# Initialize the Gemini client
client = genai.Client(api_key=settings.gemini_api_key)

async def generate_advice(user_id: str, limit: int = 5) -> str:
    """
    Generate advice based on both workout history and posture analysis.
    """
    # 1. Retrieve recent workout sessions
    workout_sessions = []
    cursor = db.sessions.find({"user_id": user_id}).sort("finished_at", -1).limit(limit)
    async for doc in cursor:
        workout_sessions.append(doc)

    # 2. Retrieve posture analysis data
    posture_sessions = []
    cursor = db.posture_sessions.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    async for doc in cursor:
        posture_sessions.append(doc)

    # 3. Build workout history summary
    workout_summary = []
    for s in workout_sessions:
        workout_lines = [f"Session on {s.get('finished_at', '')}:"]
        for w in s['workouts']:
            sets_info = [f"{st['reps']} reps @ {st['weight']} lbs" for st in w['sets']]
            workout_lines.append(f"  - {w['name']}: {', '.join(sets_info)}")
        workout_summary.extend(workout_lines)

    # 4. Build posture analysis summary
    form_issues = []
    for p in posture_sessions:
        for set_data in p.get('sets', []):
            metrics = set_data.get('form_metrics', {})
            if metrics.get('elbow_flare', 0) > 15:
                form_issues.append("excessive elbow flare")
            if metrics.get('torso_lean', 0) > 10:
                form_issues.append("significant torso lean")
            if metrics.get('rom_percentage', 0) < 80:
                form_issues.append("incomplete range of motion")
            if metrics.get('shoulder_elevation', 0) > 0.1:
                form_issues.append("shoulder shrugging")

    # 5. Create enhanced prompt for Gemini
    prompt = f"""
Based on the user's workout history and form analysis:

Recent Workout History:
{chr(10).join(workout_summary)}

Form Analysis Issues:
- {', '.join(form_issues) if form_issues else 'No major form issues detected'}

Please provide specific advice addressing:
1. Exercise progression and weight selection
2. Form corrections needed based on the analysis
3. Injury prevention recommendations
4. Suggested modifications to improve technique

Keep the response focused and actionable and as brief as possible no more than 1 line.
"""

    # 6. Call Gemini chat API
    chat = client.chats.create(model="gemini-2.0-flash-001")
    response = chat.send_message(prompt)
    return response.text
