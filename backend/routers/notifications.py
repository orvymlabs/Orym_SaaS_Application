from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Notification, User
from services import decode_token
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return int(payload.get("sub", 0))


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    type: str
    title: str
    message: str


@router.get("", response_model=List[NotificationOut])
def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user notifications."""
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications


@router.get("/unread-count")
def get_unread_count(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications."""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False
    ).count()
    return {"count": count}


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(404, "Notification not found")

    notification.read = True
    db.commit()
    return {"status": "ok"}


@router.patch("/mark-all-read")
def mark_all_as_read(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False
    ).update({"read": True})
    db.commit()
    return {"status": "ok"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(404, "Notification not found")

    db.delete(notification)
    db.commit()
    return {"status": "ok"}


def create_notification(db: Session, user_id: int, type: str, title: str, message: str):
    """Helper function to create a notification."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message
    )
    db.add(notification)
    db.commit()
    logger.info(f"Created notification for user {user_id}: {type} - {title}")
    return notification
