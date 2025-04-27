import asyncio
import random
from datetime import datetime, timedelta
from app.database import db

# Test users and workout names
USERS = ['user_1', 'user_2', 'user_3']
WORKOUT_NAMES = ['Bench Press', 'Squat', 'Deadlift', 'Overhead Press', 'Pull-Up', 'Row']

async def generate_workout_sessions():
    """Generate workout session history"""
    print("Generating workout sessions...")
    await db.sessions.delete_many({})

    for user in USERS:
        for days_ago in range(1, 6):
            date = datetime.utcnow() - timedelta(days=days_ago)
            num_workouts = random.randint(1, 4)
            workouts = []
            
            for _ in range(num_workouts):
                name = random.choice(WORKOUT_NAMES)
                num_sets = random.randint(2, 5)
                sets = [
                    {
                        'reps': random.randint(5, 12),
                        'weight': round(random.uniform(100, 300), 1)
                    }
                    for _ in range(num_sets)
                ]
                workouts.append({'name': name, 'sets': sets})

            session_doc = {
                'user_id': user,
                'workouts': workouts,
                'finished_at': date.isoformat()
            }
            res = await db.sessions.insert_one(session_doc)
            print(f"Inserted workout session {res.inserted_id} for {user} on {date.date()}")

async def generate_posture_data():
    """Generate posture analysis history"""
    print("\nGenerating posture analysis data...")
    await db.posture_sessions.delete_many({})

    for user in USERS:
        for days_ago in range(1, 6):
            date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Generate 2-3 posture sessions per day
            for session in range(random.randint(2, 3)):
                num_sets = random.randint(3, 5)
                sets = []
                
                for set_num in range(num_sets):
                    # Generate random but realistic form metrics
                    set_metrics = {
                        "set_number": set_num + 1,
                        "reps": random.randint(8, 12),
                        "form_metrics": {
                            "elbow_flare": round(random.uniform(5, 25), 2),
                            "torso_lean": round(random.uniform(3, 15), 2),
                            "shoulder_elevation": round(random.uniform(0.05, 0.2), 2),
                            "rom_percentage": round(random.uniform(75, 100), 2)
                        }
                    }
                    sets.append(set_metrics)

                posture_doc = {
                    "user_id": user,
                    "timestamp": (date + timedelta(hours=session)).isoformat(),
                    "exercise": "Bicep Curl",
                    "sets": sets,
                    "sessionSummary": {
                        "totalReps": sum(s["reps"] for s in sets),
                        "avgFormScore": round(random.uniform(6, 9), 1),
                        "primaryIssues": random.sample([
                            "elbow flare", 
                            "shoulder elevation",
                            "incomplete ROM",
                            "torso swaying"
                        ], k=random.randint(1, 2))
                    }
                }
                
                res = await db.posture_sessions.insert_one(posture_doc)
                print(f"Inserted posture session {res.inserted_id} for {user} on {date.date()}")

async def main():
    """Populate both workout and posture data"""
    try:
        # Generate both types of data
        await generate_workout_sessions()
        await generate_posture_data()
        
        # Print final counts
        workout_count = await db.sessions.count_documents({})
        posture_count = await db.posture_sessions.count_documents({})
        
        print("\nPopulation complete!")
        print(f"Total workout sessions: {workout_count}")
        print(f"Total posture sessions: {posture_count}")
        
    except Exception as e:
        print(f"Error populating database: {e}")

if __name__ == "__main__":
    asyncio.run(main())