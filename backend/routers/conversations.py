from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from database import get_db
from models import Message, Lead, Bot, Integration
from services import decode_token
from typing import List, Dict

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return int(payload.get("sub", 0))


@router.get("/")
async def get_conversations(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all conversations (unique phone numbers) with message counts and bot info for the current user."""
    user_id = get_current_user_id(request)

    # Get user's bot
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return []

    # Get all messages grouped by phone number
    conversations = db.query(
        Message.phone_number,
        func.count(Message.id).label("message_count"),
        func.max(Message.timestamp).label("last_message_at"),
        func.max(Message.message).label("last_message")
    ).filter(
        Message.bot_id == bot.id
    ).group_by(
        Message.phone_number
    ).order_by(
        func.max(Message.timestamp).desc()
    ).all()

    # Get integration for WhatsApp number
    integration = db.query(Integration).filter(Integration.bot_id == bot.id).first()
    whatsapp_number = integration.whatsapp_number if integration else None

    result = []
    for conv in conversations:
        # Find lead info if available
        lead = db.query(Lead).filter(
            Lead.bot_id == bot.id,
            Lead.phone == conv.phone_number
        ).first()

        result.append({
            "phone": conv.phone_number,
            "message_count": conv.message_count,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "last_message": conv.last_message,
            "contact_name": lead.name if lead else None,
            "bot_id": bot.id,
            "bot_mode": bot.mode,
            "bot_status": bot.status,
            "whatsapp_number": whatsapp_number,
        })

    return result


@router.get("/summary")
async def get_conversations_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get conversation summary stats for the current user."""
    user_id = get_current_user_id(request)

    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return {
            "total_conversations": 0,
            "total_messages": 0,
            "unique_contacts": 0,
        }

    total_messages = db.query(func.count(Message.id)).filter(Message.bot_id == bot.id).scalar()
    unique_contacts = db.query(func.count(distinct(Message.phone_number))).filter(Message.bot_id == bot.id).scalar()

    return {
        "total_conversations": unique_contacts,
        "total_messages": total_messages or 0,
        "unique_contacts": unique_contacts or 0,
        "bot_status": bot.status,
        "bot_mode": bot.mode,
    }
