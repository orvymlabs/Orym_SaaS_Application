from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Lead, Bot
from services import decode_token
from typing import List, Optional

router = APIRouter(prefix="/api/leads", tags=["leads"])


def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return int(payload.get("sub", 0))


@router.get("/")
def get_leads(
    request: Request,
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """Get all leads for the current user's bot, excluding customers who have placed orders."""
    from models import Order
    user_id = get_current_user_id(request)

    # Get user's bot
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return []

    # Get phone numbers that have placed orders
    order_phones = db.query(Order.phone).filter(Order.user_id == user_id).distinct().all()
    order_phone_list = [phone[0] for phone in order_phones]

    # Get all leads for this bot, excluding those who have placed orders
    leads_query = db.query(Lead).filter(Lead.bot_id == bot.id)

    # Exclude leads whose phone numbers appear in orders
    if order_phone_list:
        leads_query = leads_query.filter(~Lead.phone.in_(order_phone_list))

    leads = leads_query.order_by(Lead.updated_at.desc()).limit(limit).all()

    # Format leads with interest level
    result = []
    for lead in leads:
        context = lead.context or {}
        result.append({
            "id": lead.id,
            "phone": lead.phone,
            "name": lead.name,
            "last_message": lead.last_message,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "interest_level": context.get("interest_level", "unknown"),
            "requested_contact": context.get("requested_contact", False),
            "last_query": context.get("last_query", ""),
        })

    return result


@router.get("/{lead_id}")
def get_lead(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a specific lead by ID."""
    user_id = get_current_user_id(request)

    # Get user's bot
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")

    # Get lead
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.bot_id == bot.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    context = lead.context or {}
    return {
        "id": lead.id,
        "phone": lead.phone,
        "name": lead.name,
        "last_message": lead.last_message,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        "interest_level": context.get("interest_level", "unknown"),
        "requested_contact": context.get("requested_contact", False),
        "last_query": context.get("last_query", ""),
    }


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a lead."""
    user_id = get_current_user_id(request)

    # Get user's bot
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")

    # Get lead
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.bot_id == bot.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    db.delete(lead)
    db.commit()

    return {"status": "ok", "message": "Lead deleted"}
