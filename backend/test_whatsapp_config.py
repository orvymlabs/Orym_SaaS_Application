"""
WhatsApp Configuration Diagnostic Tool
Run this to verify your WhatsApp setup is correct
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Integration, Bot, User
from services.encryption import decrypt_value
import requests

def test_whatsapp_config():
    print("=" * 60)
    print("WhatsApp Configuration Diagnostic Tool")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Get all integrations
        integrations = db.query(Integration).join(Bot).join(User).all()

        if not integrations:
            print("[X] No integrations found in database")
            return

        print(f"\n[OK] Found {len(integrations)} integration(s)\n")

        for idx, integ in enumerate(integrations, 1):
            print(f"\n{'='*60}")
            print(f"Integration #{idx} (ID: {integ.id})")
            print(f"{'='*60}")

            # Bot info
            bot = integ.bot
            user = bot.owner
            print(f"\nUser: {user.email}")
            print(f"Bot ID: {bot.id}")
            print(f"Bot Mode: {bot.mode}")
            print(f"Bot Status: {'ACTIVE' if bot.status else 'INACTIVE'}")

            # WhatsApp Configuration
            print(f"\nWhatsApp Configuration:")
            print(f"   Phone Number ID: {integ.phone_number_id or '[NOT SET]'}")
            print(f"   WhatsApp Number: {integ.whatsapp_number or '[NOT SET]'}")
            print(f"   Verify Token: {integ.verify_token or '[NOT SET]'}")

            # Check WhatsApp Token
            if integ.whatsapp_token:
                try:
                    decrypted_token = decrypt_value(integ.whatsapp_token)
                    token_preview = decrypted_token[:20] + "..." if len(decrypted_token) > 20 else decrypted_token
                    print(f"   Access Token: [OK] SET ({token_preview})")

                    # Test the token with Meta API
                    print(f"\nTesting WhatsApp Access Token...")
                    test_url = f"https://graph.facebook.com/v21.0/{integ.phone_number_id}"
                    headers = {"Authorization": f"Bearer {decrypted_token}"}

                    try:
                        response = requests.get(test_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            print(f"   [OK] Token is VALID")
                            print(f"   Phone: {data.get('display_phone_number', 'N/A')}")
                            print(f"   Verified: {data.get('verified_name', 'N/A')}")
                        elif response.status_code == 401:
                            print(f"   [X] Token is INVALID or EXPIRED")
                            print(f"   Error: {response.json()}")
                        else:
                            print(f"   [!] Unexpected response: {response.status_code}")
                            print(f"   Response: {response.text[:200]}")
                    except requests.exceptions.RequestException as e:
                        print(f"   [!] Could not test token: {e}")

                except Exception as e:
                    print(f"   [X] Error decrypting token: {e}")
            else:
                print(f"   Access Token: [NOT SET]")

            # Website Configuration
            print(f"\nWebsite Configuration:")
            print(f"   Business Type: {integ.business_type or 'product'}")
            print(f"   WooCommerce URL: {integ.woocommerce_url or 'Not set'}")
            print(f"   WordPress URL: {integ.wp_base_url or 'Not set'}")

            # Webhook URL
            print(f"\nWebhook Configuration:")
            print(f"   Webhook URL: https://expulsive-unoperating-cordie.ngrok-free.dev/webhook")
            print(f"   Verify Token: {integ.verify_token or 'NOT SET'}")

            # Configuration Status
            print(f"\nConfiguration Status:")
            issues = []

            if not integ.phone_number_id:
                issues.append("[X] Phone Number ID is missing")
            if not integ.whatsapp_token:
                issues.append("[X] WhatsApp Access Token is missing")
            if not integ.verify_token:
                issues.append("[X] Verify Token is missing")
            if not bot.status:
                issues.append("[!] Bot is inactive")

            if issues:
                print("   Issues found:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("   [OK] All required fields are configured!")

            print(f"\n{'='*60}\n")

        print("\nNext Steps:")
        print("1. Make sure all required fields are filled in the Integrations page")
        print("2. Configure webhook in Meta Developer Console:")
        print("   - Callback URL: https://expulsive-unoperating-cordie.ngrok-free.dev/webhook")
        print("   - Verify Token: (use the token shown above)")
        print("   - Subscribe to: messages")
        print("3. Make sure your bot is Active (toggle in dashboard)")
        print("4. Send a test message to your WhatsApp number")

    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_whatsapp_config()
