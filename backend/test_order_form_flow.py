"""
Test Order Form Template Flow
Verify that the bot sends the user's custom order form template instead of hardcoded default.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import Bot, BotSettings, Integration
from services.bot_engine import handle_message
from services.encryption import decrypt_value

def test_order_form_template():
    db = SessionLocal()
    try:
        # Get bot with ID 2 (has custom template set)
        bot = db.query(Bot).filter(Bot.id == 2).first()
        if not bot:
            print("ERROR: Bot ID 2 not found in database")
            return

        print(f"[OK] Testing with Bot ID: {bot.id}")
        print(f"[OK] Bot Mode: {bot.mode}")

        # Get bot settings
        if not bot.settings:
            print("ERROR: No bot settings found")
            return

        # Force refresh from database
        db.refresh(bot.settings)

        print(f"\n[DATABASE] Current Order Form Template:")
        if bot.settings.order_form_template:
            print(bot.settings.order_form_template)
            print(f"\n[OK] Template length: {len(bot.settings.order_form_template)} characters")
            print(f"[OK] Contains 'vehicle number': {'vehicle number' in bot.settings.order_form_template}")
            print(f"[OK] Contains 'car name': {'car name' in bot.settings.order_form_template}")
        else:
            print("[WARNING] No custom template saved (will use default)")

        # Get integration for contact info
        integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()

        # Prepare bot settings dict (same as webhook does)
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
            "template_statuses": bot.settings.template_statuses if bot.settings else {},
            "custom_products": bot.settings.custom_products if bot.settings else [],
            "order_form_template": bot.settings.order_form_template if bot.settings else None,
            "order_confirmation_message": bot.settings.order_confirmation_message if bot.settings else None,
            "order_form_enabled": bot.settings.order_form_enabled if bot.settings and bot.settings.order_form_enabled is not None else True,
            "_bot_id": bot.id
        }

        contact_info = {
            "site_name": "Test Store",
            "phone": "+1234567890",
            "email": "test@example.com",
            "address": "123 Test St"
        }

        # Simulate customer sending "order"
        print("\n[TEST] Simulating customer message: 'order'")
        reply = handle_message(
            bot_mode=bot.mode,
            bot_id=bot.id,
            text="order",
            phone="+1234567890",
            name="Test Customer",
            bot_settings=bot_settings,
            integrations={},
            contact_info=contact_info,
            products=[],
            categories=[],
            business_type=integ.business_type if integ else "product",
            user_plan="starter",
            user_id=bot.user_id
        )

        print("\n[BOT REPLY]:")
        print(reply)

        # Verify the reply contains custom fields
        print("\n[VERIFICATION]:")
        if "vehicle number" in reply.lower():
            print("[SUCCESS] Reply contains 'vehicle number' - CUSTOM TEMPLATE WORKING!")
        else:
            print("[FAIL] Reply does NOT contain 'vehicle number' - Still using old template")

        if "car name" in reply.lower():
            print("[SUCCESS] Reply contains 'car name' - CUSTOM TEMPLATE WORKING!")
        else:
            print("[FAIL] Reply does NOT contain 'car name' - Still using old template")

        # Check if it contains old fields that should NOT be there
        if "Product / Item:" in reply:
            print("[WARNING] Reply still contains 'Product / Item:' - Old template detected")

        if "Special Instructions" in reply:
            print("[WARNING] Reply still contains 'Special Instructions' - Old template detected")

    finally:
        db.close()

if __name__ == "__main__":
    test_order_form_template()
