# File: app/models.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

#
# —— JournalEntry Models —— 
#
class JournalEntryBase(BaseModel):
    content: str = Field(..., description="Text of the journal entry")
    user_id: Optional[str] = Field(
        None, description="(Optional) ID of the authoring user"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Today I hit a new PR on squat! Feeling strong and motivated.",
                "user_id": "user_12345",
            }
        }
    )

class JournalEntryCreate(JournalEntryBase):
    """Use this for POST /entries"""

class JournalEntryUpdate(BaseModel):
    """Use this for PUT /entries/{id}"""
    content: Optional[str] = None
    user_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Updated entry content.",
                "user_id": "user_12345",
            }
        }
    )

class JournalEntry(JournalEntryBase):
    """This is the full model returned by GET/PUT/POST"""
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,    # allow passing id via "_id"
        json_schema_extra={
            "example": {
                "_id": "6523a1f8e13f4c001e3a9b4d",
                "content": "Today I hit a new PR on squat! Feeling strong.",
                "user_id": "user_12345",
                "created_at": "2025-04-27T02:15:00Z"
            }
        },
    )


#
# —— PostureData Models —— 
#
class PostureDataBase(BaseModel):
    elbow_angle:    float = Field(..., description="Elbow angle in degrees")
    hip_angle:      float = Field(..., description="Hip angle in degrees")
    knee_angle:     float = Field(..., description="Knee angle in degrees")
    shoulder_angle: float = Field(..., description="Shoulder angle in degrees")
    user_id: Optional[str] = Field(
        None, description="(Optional) ID of the user being tracked"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "elbow_angle": 45.0,
                "hip_angle": 175.0,
                "knee_angle": 170.0,
                "shoulder_angle": 30.0,
                "user_id": "user_12345"
            }
        }
    )

class PostureDataCreate(PostureDataBase):
    """Use this for POST /posture"""

class PostureData(PostureDataBase):
    """Returned by GET/POST posture endpoints"""
    id: str = Field(..., alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "6523a1f8e13f4c001e3a9b4e",
                "elbow_angle": 45.0,
                "hip_angle": 175.0,
                "knee_angle": 170.0,
                "shoulder_angle": 30.0,
                "user_id": "user_12345",
                "timestamp": "2025-04-27T02:16:00Z"
            }
        },
    )


#
# —— Workout Session Models —— 
#
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class Set(BaseModel):
    """Individual set data"""
    reps: int
    weight: float

class Workout(BaseModel):
    """Single workout with multiple sets"""
    name: str
    sets: List[Set]

class Session(BaseModel):
    """Workout session creation request"""
    user_id: str
    workouts: List[Workout]
    notes: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user12345",
                "workouts": [
                    {
                        "name": "Bench Press",
                        "sets": [
                            {"reps": 8, "weight": 185.0},
                            {"reps": 6, "weight": 195.0}
                        ]
                    }
                ],
                "notes": "Good session, increased weight on bench"
            }
        }
    )


# Add this after the Session class and before SessionEntryBase
class SessionEntryCreate(Session):
    """Model for creating new session entries"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user12345",
                "workouts": [
                    {
                        "name": "Bench Press",
                        "sets": [
                            {"reps": 8, "weight": 185.0},
                            {"reps": 6, "weight": 195.0}
                        ]
                    }
                ],
                "notes": "Initial session entry"
            }
        }
    )
class SessionEntryBase(Session):
    """Base class for session entries"""
    pass

class SessionEntry(SessionEntryBase):
    """Full session returned by GET/PUT/POST"""
    id: str = Field(..., alias="_id")
    finished_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "20250427_user12345",
                "user_id": "user12345",
                "workouts": [
                    {
                        "name": "Bench Press",
                        "sets": [
                            {"reps": 8, "weight": 185.0},
                            {"reps": 6, "weight": 195.0}
                        ]
                    }
                ],
                "finished_at": "2025-04-27T15:30:00Z"
            }
        }
    )

class SessionEntryUpdate(BaseModel):
    """Fields that can be updated"""
    notes: Optional[str] = None
    workouts: Optional[List[Workout]] = None
#
# —— Advice Models —— 
#
class AdviceResponse(BaseModel):
    """The AI-generated advice for a user."""
    advice: str = Field(..., description="Personalized workout advice from the AI")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "advice": "Try increasing your bench press by 5 lbs next session, "
                          "and swap in incline presses to shock your chest muscles."
            }
        }
    )