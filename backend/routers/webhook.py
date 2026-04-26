"""
WhatsApp Webhook — Production Multi-tenant SaaS Platform.
"""
import hashlib
import hmac
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models import Integration, Bot, User, Message
from services.encryption import decrypt_value
from services.whatsapp import send_whatsapp_text, mark_message_as_read
from services.bot_engine import handle_message
from config import get_settings
from services.universal_website_fetcher import UniversalWebsiteFetcher

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

settings = get_settings()
IS_PRODUCTION = settings.ENVIRONMENT == "production"


def process_whatsapp_message_background(
    db: Session,
    phone_number_id: str,
    from_num: str,
    text: str,
    contact_info: Dict[str, Any],
    webhook_id: str
) -> None:
    """Process WhatsApp message in background (fetch products, call AI, send reply)."""
    try:
        # Find integration
        integ = db.query(Integration).filter(Integration.phone_number_id == phone_number_id).first()
        if not integ or not integ.bot:
            logger.warning(f"[{webhook_id}] No integration/bot found for {phone_number_id}")
            db.close()
            return

        bot = integ.bot
        if not bot.status:
            logger.info(f"[{webhook_id}] Bot is inactive for {phone_number_id}")
            db.close()
            return

        wa_token = decrypt_value(integ.whatsapp_token) if integ.whatsapp_token else None

        # Fetch products and site info from website
        products, categories = [], []
        contact_info_data = {}
        try:
            if integ.woocommerce_url:
                # 1. Fetch products
                fetcher_data = UniversalWebsiteFetcher.scrape_products_from_website(integ.woocommerce_url)
                products = fetcher_data.get("products", [])
                categories = fetcher_data.get("categories", [])
                logger.info(f"[{webhook_id}] Fetched {len(products)} products from {integ.woocommerce_url}")
                
                # 2. Fetch site info (contact, about, services)
                site_info = UniversalWebsiteFetcher.fetch_site_info(integ.woocommerce_url)
                contact_info_data = {
                    "site_name": site_info.get("site_name") or integ.woocommerce_url,
                    "site_description": site_info.get("site_description", ""),
                    "about": site_info.get("about", ""),
                    "services": site_info.get("services", []),
                    "phone": site_info.get("contact", {}).get("phone", ""),
                    "email": site_info.get("contact", {}).get("email", ""),
                    "address": site_info.get("contact", {}).get("address", ""),
                    "hours": site_info.get("contact", {}).get("hours", "")
                }
                logger.info(f"[{webhook_id}] Fetched site info for {integ.woocommerce_url}")
        except Exception as e:
            logger.error(f"[{webhook_id}] Website data fetch error: {e}")

        # Bot settings
        bot_settings = {
            "prompt": bot.settings.prompt if bot.settings else "",
            "model_name": bot.settings.model_name if bot.settings else "openrouter",
            "specific_model_name": bot.settings.specific_model_name if bot.settings else None,
            "api_key": decrypt_value(bot.settings.api_key) if bot.settings and bot.settings.api_key else "",
            "temperature": bot.settings.temperature if bot.settings else 70,
            "language": bot.settings.language if bot.settings else "english",
            "templates": bot.settings.templates if bot.settings else {},
            "custom_responses": bot.settings.custom_responses if bot.settings else {},
            "template_enabled": getattr(bot.settings, 'template_enabled', True) if bot.settings else True,
            "custom_products": bot.settings.custom_products if bot.settings else []
        }

        # User plan
        user = db.query(User).filter(User.id == bot.user_id).first()
        user_plan = user.plan if user else "starter"

        # Call bot engine - FIXING KEYWORD ARGUMENTS
        reply = handle_message(
            bot_mode=bot.mode,
            bot_id=bot.id,
            text=text,
            phone=from_num,
            name=contact_info.get("name", "Friend"),
            bot_settings=bot_settings,
            integrations={"whatsapp_token": wa_token, "phone_number_id": phone_number_id},
            contact_info=contact_info_data,
            products=products,
            categories=categories,
            business_type=integ.business_type or "product",
            user_plan=user_plan
        )

        # Send reply and save to database with WhatsApp message ID
        if reply and wa_token and phone_number_id:
            logger.info(f"[{webhook_id}] Sending reply to {from_num}: {reply[:50]}...")

            result = send_whatsapp_text(from_num, reply, wa_token, phone_number_id)
            whatsapp_msg_id = result.get("message_id") if result else None

            # Save bot reply to database with WhatsApp message ID for tracking
            bot_msg = Message(
                bot_id=bot.id,
                sender="bot",
                phone_number=from_num,
                message=reply[:1000],  # Truncate long messages
                whatsapp_message_id=whatsapp_msg_id,  # Store WhatsApp message ID for read receipts
                seen=False  # Bot message not seen by user yet
            )
            db.add(bot_msg)
            db.commit()
            logger.info(f"[{webhook_id}] Saved bot message {bot_msg.id} with WhatsApp ID: {whatsapp_msg_id}")

        db.close()

    except Exception as e:
        logger.error(f"[{webhook_id}] Background processing error: {str(e)}", exc_info=True)


def validate_webhook_signature(payload: bytes, signature: str | None, app_secret: str) -> bool:
    """
    Validate Meta webhook signature using HMAC-SHA256.
    Meta uses the App Secret (not verify_token) for POST request signatures.
    """
    logger.debug(f"Validating signature. Payload (truncated): {payload[:200]!r}... Signature: {signature!r}")
    if not signature:
        logger.warning("Signature is missing.")
        return False
    try:
        method, expected = signature.split("=")
        if method != "sha256":
            logger.warning(f"Invalid signature method: {method}. Expected 'sha256'.")
            return False
        # Meta uses App Secret for HMAC signature
        computed = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
        logger.debug(f"Computed HMAC: {computed}, Expected HMAC: {expected}")
        is_valid = hmac.compare_digest(computed, expected)
        logger.debug(f"Signature validation result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error during signature validation: {e}", exc_info=True)
        return False


@router.get("")
async def webhook_verify(request: Request, db: Session = Depends(get_db)):
    """
    Verify webhook for Meta/Facebook App setup.
    Meta sends a GET request with hub.mode=subscribe and a verify_token.
    We must return the hub.challenge string if verification succeeds.
    """
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification request: mode={mode}, verify_token={verify_token}")

    # Log default verify token for debugging
    logger.debug(f"Default verify token from settings: {settings.DEFAULT_VERIFY_TOKEN}")

    if mode == "subscribe" and verify_token:
        # Check against default verify token
        if verify_token == settings.DEFAULT_VERIFY_TOKEN:
            logger.info("Webhook verification successful with default token")
            return PlainTextResponse(content=challenge)

        # Check against user's verify token in database
        try:
            integ = db.query(Integration).filter(Integration.verify_token == verify_token).first()
            if integ:
                logger.info(f"Webhook verification successful for integration ID: {integ.id}")
                return PlainTextResponse(content=challenge)
        except Exception as e:
            logger.error(f"Webhook verification DB lookup failed: {e}")

    logger.warning(f"Webhook verification failed: mode={mode}, token={verify_token}")
    return PlainTextResponse(status_code=403, content="Verification failed")


@router.post("")
async def webhook_post(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp messages.
    Returns immediately and processes message in background to avoid timeout.
    """
    webhook_id = f"wh_{datetime.now().strftime('%H%M%S')}"

    try:
        raw_body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")

        # Log relevant details for debugging signature validation
        logger.debug(f"[{webhook_id}] Raw request body: {raw_body.decode('utf-8', errors='ignore')}")
        logger.debug(f"[{webhook_id}] Received X-Hub-Signature-256: {signature}")
        logger.debug(f"[{webhook_id}] META_APP_SECRET from settings: {settings.META_APP_SECRET[:10] if settings.META_APP_SECRET else 'NOT SET'}...")
        logger.debug(f"[{webhook_id}] IS_PRODUCTION flag: {IS_PRODUCTION}")

        # Skip signature validation if META_APP_SECRET is not configured (development)
        if IS_PRODUCTION and settings.META_APP_SECRET:
            if not validate_webhook_signature(raw_body, signature, settings.META_APP_SECRET):
                # Recompute and log computed signature if validation fails
                try:
                    if signature:
                        method, expected = signature.split("=")
                        if method == "sha256":
                            computed_for_log = hmac.new(settings.META_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
                            logger.warning(f"[{webhook_id}] Signature mismatch: Computed={computed_for_log}, Expected={expected}")
                        else:
                            logger.warning(f"[{webhook_id}] Invalid signature method: {method}")
                    else:
                        logger.warning(f"[{webhook_id}] Signature header is missing.")
                except Exception as log_e:
                    logger.error(f"[{webhook_id}] Error during signature logging: {log_e}")

                logger.warning(f"[{webhook_id}] Invalid signature")
                return JSONResponse(status_code=403, content={"error": "Invalid signature"})
        elif IS_PRODUCTION:
            logger.warning(f"[{webhook_id}] Production mode but META_APP_SECRET not configured - skipping signature validation")

        data = json.loads(raw_body)

        # Validation - ensure it's a WhatsApp Business Account webhook
        if not isinstance(data, dict) or data.get("object") != "whatsapp_business_account":
            return {"status": "ok"}

        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Handle message status updates (delivered, read)
        statuses = value.get("statuses", [])
        if statuses:
            for status in statuses:
                status_type = status.get("status")  # "sent", "delivered", "read"
                whatsapp_msg_id = status.get("id")  # WhatsApp message ID
                recipient_id = status.get("recipient_id")

                if status_type == "read" and whatsapp_msg_id:
                    # Update bot message as seen in database using WhatsApp message ID
                    db_msg = db.query(Message).filter(
                        Message.whatsapp_message_id == whatsapp_msg_id
                    ).first()
                    if db_msg:
                        db_msg.seen = True
                        db.commit()
                        logger.info(f"[{webhook_id}] Message {db_msg.id} marked as seen by recipient {recipient_id}")

            return {"status": "ok"}

        messages = value.get("messages", [])

        # Ignore non-text messages - return immediately
        if not messages or messages[0].get("type") != "text":
            logger.info(f"[{webhook_id}] Ignoring non-text message")
            return {"status": "ok"}

        msg = messages[0]
        from_num = msg.get("from")
        text = msg.get("text", {}).get("body", "").strip()
        metadata = value.get("metadata", {})
        phone_number_id = metadata.get("phone_number_id")
        contact_info = value.get("contacts", [{}])[0].get("profile", {})

        # Verify integration exists before queueing background task
        integ = db.query(Integration).filter(Integration.phone_number_id == phone_number_id).first()
        if not integ or not integ.bot:
            logger.warning(f"[{webhook_id}] No integration/bot found for {phone_number_id}")
            return {"status": "ok"}

        if not integ.bot.status:
            logger.info(f"[{webhook_id}] Bot is inactive for {phone_number_id}")
            return {"status": "ok"}

        # Decrypt WhatsApp token for marking messages as read
        wa_token = decrypt_value(integ.whatsapp_token) if integ.whatsapp_token else None

        # Save incoming user message to database (not seen yet)
        user_msg = Message(
            bot_id=integ.bot.id,
            sender="user",
            phone_number=from_num,
            message=text,
            seen=False  # Not seen until bot processes it
        )
        db.add(user_msg)
        db.commit()
        logger.info(f"[{webhook_id}] Saved user message {user_msg.id}")

        # Mark user message as seen in WhatsApp API
        if wa_token and phone_number_id and user_msg.id:
            try:
                # Get the WhatsApp message ID from the webhook if available
                wa_msg_id = msg.get("id")
                if wa_msg_id:
                    mark_message_as_read(wa_msg_id, wa_token, phone_number_id)
                # Update DB to show we've marked it as read
                user_msg.seen = True
                db.commit()
                logger.info(f"[{webhook_id}] Marked message {user_msg.id} as read via WhatsApp API")
            except Exception as e:
                logger.debug(f"[{webhook_id}] Failed to mark as read: {e}")

        # Queue background task to process the message
        # Create a new DB session for the background task
        bg_db = next(get_db())
        background_tasks.add_task(
            process_whatsapp_message_background,
            bg_db,
            phone_number_id,
            from_num,
            text,
            contact_info,
            webhook_id
        )

        logger.info(f"[{webhook_id}] Message queued for processing: from={from_num}, text={text[:30]}...")

        # Return immediately to Meta (within 3 seconds)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"[{webhook_id}] CRITICAL ERROR: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
