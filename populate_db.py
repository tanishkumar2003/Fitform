# File: populate_db.py

import asyncio
import random
from datetime import datetime, timedelta
from app.database import db

# List of test users
USERS = ['user_1', 'user_2', 'user_3']

# Example workout names
WORKOUT_NAMES = ['Bench Press', 'Squat', 'Deadlift', 'Overhead Press', 'Pull-Up', 'Row']

async def main():
    # Clear existing sessions (optional)
    print("Clearing existing test sessions...")
    await db.sessions.delete_many({})

    # For each user, create 5 past sessions
    for user in USERS:
        for days_ago in range(1, 6):
            # Build a sample date/time
            date = datetime.utcnow() - timedelta(days=days_ago)
            # Random number of workouts per session
            num_workouts = random.randint(1, 4)
            workouts = []
            for _ in range(num_workouts):
                name = random.choice(WORKOUT_NAMES)
                # Random number of sets per workout
                num_sets = random.randint(2, 5)
                sets = [
                    {
                        'reps': random.randint(5, 12),
                        'weight': round(random.uniform(100, 300), 1)
                    }
                    for _ in range(num_sets)
                ]
                workouts.append({'name': name, 'sets': sets})

            # Insert session document
            session_doc = {
                'user_id': user,
                'workouts': workouts,
                'finished_at': date.isoformat()
            }
            res = await db.sessions.insert_one(session_doc)
            print(f"Inserted session {res.inserted_id} for {user} on {date.date()}")

    print("Done populating test data.")

if __name__ == "__main__":
    asyncio.run(main())
