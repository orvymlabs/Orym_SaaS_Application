"""
Test Order Confirmation Message Flow
Verify that the bot sends the user's custom confirmation message after order submission.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import Bot, BotSettings, Integration, Lead
from services.bot_engine import handle_message
from services.encryption import decrypt_value
from sqlalchemy.orm.attributes import flag_modified

def test_order_confirmation():
    db = SessionLocal()
    try:
        # Get bot with ID 2 (has custom template set)
        bot = db.query(Bot).filter(Bot.id == 2).first()
        if not bot:
            print("ERROR: Bot ID 2 not found in database")
            return

        print(f"[OK] Testing with Bot ID: {bot.id}")

        # Force refresh from database
        db.refresh(bot.settings)

        print(f"\n[DATABASE] Current Order Confirmation Message:")
        if bot.settings.order_confirmation_message:
            print(bot.settings.order_confirmation_message)
        else:
            print("[WARNING] No custom confirmation message saved")

        # Get integration
        integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()

        # Prepare bot settings dict
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

        test_phone = "+1234567890"

        # Step 1: Start order flow
        print("\n[TEST STEP 1] Customer sends: 'order'")
        reply1 = handle_message(
            bot_mode=bot.mode,
            bot_id=bot.id,
            text="order",
            phone=test_phone,
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
        print("[BOT REPLY 1 - FULL]:")
        print(reply1)

        # Step 2: Customer submits filled order form
        print("\n[TEST STEP 2] Customer submits filled order form")
        filled_form = """Full Name: John Doe
Phone Number: +1234567890
Delivery Address: 123 Main St
vehicle number: ABC123
car name: Toyota Camry"""

        reply2 = handle_message(
            bot_mode=bot.mode,
            bot_id=bot.id,
            text=filled_form,
            phone=test_phone,
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

        print("\n[BOT REPLY 2 - CONFIRMATION]:")
        print(reply2)

        # Verify the confirmation message
        print("\n[VERIFICATION]:")
        if bot.settings.order_confirmation_message and bot.settings.order_confirmation_message in reply2:
            print("[SUCCESS] Bot sent the custom confirmation message!")
        else:
            print("[FAIL] Bot did NOT send the custom confirmation message")

    finally:
        db.close()

if __name__ == "__main__":
    test_order_confirmation()
