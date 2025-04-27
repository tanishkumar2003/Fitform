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
    Fetch the user's most recent workout sessions, build a concise prompt,
    and return brief AI-generated tips.
    """
    # 1. Retrieve recent sessions for this user
    sessions = []
    cursor = db.sessions.find({"user_id": user_id}).sort("finished_at", -1).limit(limit)
    async for doc in cursor:
        sessions.append(doc)

    # 2. Build a summary of workout history
    summary_lines = [f"Session {s['_id']} on {s.get('finished_at', '')}:" for s in sessions]
    for idx, s in enumerate(sessions):
        lines = [
            f"  - {w['name']}: " + ", ".join([f"{st['reps']} reps @ {st['weight']} lbs" for st in w['sets']])
            for w in s['workouts']
        ]
        summary_lines.insert(2*idx+1, "\n".join(lines))
    summary = "\n".join(summary_lines)

    # 3. Create concise prompt for AI
    prompt = (
        f"User's recent workout history (last {len(sessions)} sessions):\n"
        f"{summary}\n\n"
        "Provide 1 to 2 tips for improving workouts, "
        "focusing on progressive overload and routine variation."
    )

    # 4. Call Gemini chat API
    chat = client.chats.create(model="gemini-2.0-flash-001")
    response = chat.send_message(prompt)

    # 5. Return the AI's advice text
    return response.text
