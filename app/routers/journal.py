# File: app/routers/journal.py

from fastapi import APIRouter, HTTPException, status
from typing import List

from app.crud import create_entry, get_entry, list_entries, update_entry, delete_entry
from app.models import JournalEntryCreate, JournalEntry as JournalEntryModel, JournalEntryUpdate


router = APIRouter(prefix="/entries", tags=["entries"])

# POST: accept a JournalEntryCreate, return a JournalEntryModel
@router.post("/", response_model=JournalEntryModel, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(entry: JournalEntryCreate):
    return await create_entry(entry)

# GET all
@router.get("/", response_model=List[JournalEntryModel])
async def read_entries(limit: int = 100):
    return await list_entries(limit)

# GET one
@router.get("/{entry_id}", response_model=JournalEntryModel)
async def read_entry(entry_id: str):
    entry = await get_entry(entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry

# PUT
@router.put("/{entry_id}", response_model=JournalEntryModel)
async def update_journal_entry(entry_id: str, entry: JournalEntryUpdate):
    updated = await update_entry(entry_id, entry)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found or no changes made")
    return updated

# DELETE stays the same


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(entry_id: str):
    success = await delete_entry(entry_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")
