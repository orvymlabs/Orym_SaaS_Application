"""WhatsApp Cloud API helper."""
import logging
import requests
import time

logger = logging.getLogger(__name__)


def send_whatsapp_text(to: str, text: str, token: str, phone_id: str) -> dict:
    """Send text message to WhatsApp user. Returns message ID if successful."""
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={
            "messaging_product": "whatsapp", "to": to, "type": "text",
            "text": {"body": text}
        }, timeout=15)

        if r.status_code != 200:
            logger.error(f"WhatsApp send failed: {r.status_code} {r.text[:200]}")
            return {"success": False, "message_id": None}

        response_data = r.json()
        message_id = response_data.get("messages", [{}])[0].get("id")
        logger.info(f"WhatsApp message sent, ID: {message_id}")
        return {"success": True, "message_id": message_id}
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return {"success": False, "message_id": None}


def mark_message_as_read(message_id: str, token: str, phone_id: str) -> bool:
    """Mark a specific message as read using WhatsApp API."""
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }, timeout=5)
        success = r.status_code == 200
        if success:
            logger.info(f"Message {message_id} marked as read")
        return success
    except Exception as e:
        logger.debug(f"WhatsApp mark as read error: {e}")
        return False
