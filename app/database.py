# File: app/database.py

import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

# Use certifi to supply a known-good CA bundle
_client = AsyncIOMotorClient(
    settings.mongodb_uri,
    tlsCAFile=certifi.where()
)
db = _client[settings.db_name]

def get_db():
    return db
