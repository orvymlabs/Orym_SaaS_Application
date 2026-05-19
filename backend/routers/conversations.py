from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_, cast, Date
from database import get_db
from models import Message, Lead, Bot, Integration
from services import decode_token
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

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

        # Safely handle last_message_at
        last_message_at = None
        if conv.last_message_at:
            if isinstance(conv.last_message_at, datetime):
                last_message_at = conv.last_message_at.isoformat()
            elif isinstance(conv.last_message_at, str):
                last_message_at = conv.last_message_at
            else:
                last_message_at = str(conv.last_message_at)

        result.append({
            "phone": conv.phone_number,
            "message_count": conv.message_count,
            "last_message_at": last_message_at,
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


@router.get("/analytics")
async def get_conversation_analytics(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get dynamic conversation analytics for the last N days."""
    user_id = get_current_user_id(request)

    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        return {
            "labels": [],
            "messages": [],
            "leads": [],
            "insights": {
                "peak_day": "N/A",
                "peak_time": "N/A",
                "peak_intensity": 0,
                "top_intent": "N/A",
                "top_intent_percentage": 0,
                "drop_off_point": "N/A",
                "drop_off_rate": 0
            }
        }

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    # Get messages grouped by date
    messages_by_date = db.query(
        cast(Message.timestamp, Date).label('date'),
        func.count(Message.id).label('count')
    ).filter(
        Message.bot_id == bot.id,
        Message.timestamp >= start_date
    ).group_by(
        cast(Message.timestamp, Date)
    ).all()

    # Get leads grouped by date
    leads_by_date = db.query(
        cast(Lead.created_at, Date).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.bot_id == bot.id,
        Lead.created_at >= start_date
    ).group_by(
        cast(Lead.created_at, Date)
    ).all()

    # Create date map for messages and leads
    message_map = {str(row.date): row.count for row in messages_by_date}
    lead_map = {str(row.date): row.count for row in leads_by_date}

    # Generate labels and data for all days
    labels = []
    messages_data = []
    leads_data = []

    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        label = date.strftime('%d %b')

        labels.append(label)
        messages_data.append(message_map.get(date_str, 0))
        leads_data.append(lead_map.get(date_str, 0))

    # Calculate insights
    # 1. Peak day and time
    peak_day = "N/A"
    peak_time = "N/A"
    peak_intensity = 0

    if messages_data and max(messages_data) > 0:
        peak_index = messages_data.index(max(messages_data))
        peak_date = start_date + timedelta(days=peak_index)
        peak_day = peak_date.strftime('%A')

        # Get peak hour for that day
        # Use a more robust way to get hour that works across SQLite and potentially PostgreSQL
        try:
            peak_hour_query = db.query(
                func.strftime('%H', Message.timestamp).label('hour'),
                func.count(Message.id).label('count')
            ).filter(
                Message.bot_id == bot.id,
                cast(Message.timestamp, Date) == peak_date.strftime('%Y-%m-%d')
            ).group_by(
                func.strftime('%H', Message.timestamp)
            ).order_by(
                func.count(Message.id).desc()
            ).first()

            if peak_hour_query and peak_hour_query.hour:
                hour = int(peak_hour_query.hour)
                peak_time = f"{hour % 12 or 12}{'AM' if hour < 12 else 'PM'}"
        except Exception as e:
            logger.error(f"Error calculating peak hour: {e}")
            peak_time = "N/A"

        # Calculate intensity (percentage above average)
        avg_messages = sum(messages_data) / len(messages_data) if messages_data else 1
        peak_intensity = int(((max(messages_data) - avg_messages) / avg_messages * 100)) if avg_messages > 0 else 0

    # 2. Top intent (most common message keywords)
    top_intent = "General Inquiry"
    top_intent_percentage = 0

    recent_messages = db.query(Message.message).filter(
        Message.bot_id == bot.id,
        Message.timestamp >= start_date,
        Message.sender == 'user'
    ).all()

    if recent_messages:
        # Analyze message content for common intents
        intent_keywords = {
            "Pricing Inquiry": ["price", "cost", "how much", "expensive", "cheap", "rate"],
            "Product Info": ["product", "item", "available", "stock", "catalog", "menu"],
            "Order Request": ["order", "buy", "purchase", "want to buy", "need"],
            "Contact Request": ["contact", "phone", "email", "address", "location"],
            "Delivery Info": ["delivery", "shipping", "ship", "deliver", "courier"],
            "Support": ["help", "support", "problem", "issue", "not working"]
        }

        intent_counts = defaultdict(int)
        total_analyzed = 0

        for msg in recent_messages:
            if msg.message:
                msg_lower = msg.message.lower()
                total_analyzed += 1
                matched = False
                for intent, keywords in intent_keywords.items():
                    if any(keyword in msg_lower for keyword in keywords):
                        intent_counts[intent] += 1
                        matched = True
                        break
                if not matched:
                    intent_counts["General Inquiry"] += 1

        if intent_counts:
            top_intent = max(intent_counts, key=intent_counts.get)
            top_intent_percentage = int((intent_counts[top_intent] / total_analyzed * 100)) if total_analyzed > 0 else 0

    # 3. Drop-off analysis (conversations that stopped after certain steps)
    drop_off_point = "Initial Contact"
    drop_off_rate = 0

    # Count conversations by message count
    conversation_lengths = db.query(
        func.count(Message.id).label('length')
    ).filter(
        Message.bot_id == bot.id,
        Message.timestamp >= start_date
    ).group_by(
        Message.phone_number
    ).all()

    if conversation_lengths:
        length_counts = defaultdict(int)
        for conv in conversation_lengths:
            if conv.length == 1:
                length_counts['Initial Contact'] += 1
            elif conv.length <= 3:
                length_counts['Early Stage'] += 1
            elif conv.length <= 5:
                length_counts['Mid Conversation'] += 1
            else:
                length_counts['Engaged'] += 1

        if length_counts:
            drop_off_point = max(length_counts, key=length_counts.get)
            total_convs = sum(length_counts.values())
            drop_off_rate = int((length_counts[drop_off_point] / total_convs * 100)) if total_convs > 0 else 0

    return {
        "labels": labels,
        "messages": messages_data,
        "leads": leads_data,
        "insights": {
            "peak_day": peak_day,
            "peak_time": peak_time,
            "peak_intensity": peak_intensity,
            "top_intent": top_intent,
            "top_intent_percentage": top_intent_percentage,
            "drop_off_point": drop_off_point,
            "drop_off_rate": drop_off_rate
        }
    }
