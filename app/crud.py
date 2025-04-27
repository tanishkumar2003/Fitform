# File: app/crud.py

from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.database import db

# ——— JournalEntry CRUD ———

async def create_entry(entry_data: dict) -> dict:
    """
    entry_data: Dict with keys 'content' and optional 'user_id'
    """
    result = await db.entries.insert_one(entry_data)
    created = await db.entries.find_one({"_id": result.inserted_id})
    # Convert ObjectId to string
    created["_id"] = str(created["_id"])
    return created

async def get_entry(id: str) -> Optional[dict]:
    doc = await db.entries.find_one({"_id": ObjectId(id)})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def list_entries(limit: int = 100) -> List[dict]:
    out = []
    cursor = db.entries.find().limit(limit)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out

async def update_entry(id: str, data: dict) -> Optional[dict]:
    result = await db.entries.update_one(
        {"_id": ObjectId(id)}, {"$set": data}
    )
    if result.modified_count != 1:
        return None
    updated = await db.entries.find_one({"_id": ObjectId(id)})
    updated["_id"] = str(updated["_id"])
    return updated

async def delete_entry(id: str) -> bool:
    result = await db.entries.delete_one({"_id": ObjectId(id)})
    return result.deleted_count == 1

# ——— Session (Workout) CRUD ———

async def create_session(data: dict) -> dict:
    # Remove _id if it exists in the data
    if '_id' in data:
        del data['_id']
        
    # Insert new document
    result = await db.sessions.insert_one(data)
    
    # Get the inserted document
    session = await db.sessions.find_one({"_id": result.inserted_id})
    if session:
        session["_id"] = str(session["_id"])
    return session

async def list_sessions(limit: int = 50) -> List[dict]:
    out = []
    cursor = db.sessions.find().limit(limit)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out

async def get_session(id: str) -> Optional[dict]:
    doc = await db.sessions.find_one({"_id": id})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def update_session(id: str, data: dict) -> Optional[dict]:
    result = await db.sessions.update_one({"_id": id}, {"$set": data})
    if result.modified_count != 1:
        return None
    updated = await db.sessions.find_one({"_id": id})
    updated["_id"] = str(updated["_id"])
    return updated

async def delete_session(id: str) -> bool:
    result = await db.sessions.delete_one({"_id": id})
    return result.deleted_count == 1
