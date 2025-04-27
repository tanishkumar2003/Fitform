# File: app/routers/sessions.py

from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models import SessionEntryCreate, SessionEntry, SessionEntryUpdate
from app.crud import (
    create_session,
    list_sessions,
    get_session,
    update_session,
    delete_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

from fastapi import APIRouter, HTTPException, status
from app.models import Session
from app.crud import create_session

router = APIRouter(prefix="/sessions")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def start_session(session: Session):
    try:
        result = await create_session(session.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[SessionEntry])
async def all_sessions(limit: int = 50):
    """
    List recent workout sessions.
    """
    return await list_sessions(limit)

@router.get("/{session_id}", response_model=SessionEntry)
async def one_session(session_id: str):
    sess = await get_session(session_id)
    if not sess:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess

@router.put("/{session_id}", response_model=SessionEntry)
async def edit_session(session_id: str, session: SessionEntryUpdate):
    updated = await update_session(session_id, session.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No changes or not found")
    return updated

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(session_id: str):
    success = await delete_session(session_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
