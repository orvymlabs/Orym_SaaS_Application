"""
AI Mode Diagnostic Script
Run this to check if AI mode is properly configured
"""
from database import SessionLocal
from models import SiteInfoCache, Integration, Bot, User, BotSettings
from services.encryption import decrypt_value

def check_ai_mode_setup():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("AI MODE DIAGNOSTIC CHECK")
        print("=" * 60)

        # Get first user
        user = db.query(User).first()
        if not user:
            print("\nERROR: No user found in database")
            return

        print(f"\n1. USER INFO")
        print(f"   Email: {user.email}")
        print(f"   Plan: {user.plan}")

        # Get bot
        bot = db.query(Bot).filter(Bot.user_id == user.id).first()
        if not bot:
            print("\nERROR: No bot found")
            return

        print(f"\n2. BOT CONFIGURATION")
        print(f"   Bot ID: {bot.id}")
        print(f"   Mode: {bot.mode}")
        print(f"   Status: {'Active' if bot.status else 'Inactive'}")

        if bot.mode != "ai":
            print(f"   WARNING: Bot is in '{bot.mode}' mode, not 'ai' mode!")
            print(f"   ACTION: Change bot mode to 'ai' in Bot Engine settings")

        # Check bot settings
        settings = db.query(BotSettings).filter(BotSettings.bot_id == bot.id).first()
        if settings:
            print(f"\n3. AI SETTINGS")
            has_api_key = bool(settings.api_key)
            print(f"   Has API Key: {has_api_key}")
            if has_api_key:
                try:
                    decrypted = decrypt_value(settings.api_key)
                    print(f"   API Key Preview: {decrypted[:10]}...")
                except:
                    print(f"   API Key: (encrypted, cannot preview)")
            else:
                print(f"   WARNING: No API key configured!")
                print(f"   ACTION: Add your OpenRouter/OpenAI API key in Bot Engine settings")

            print(f"   Provider: {settings.model_name or 'openrouter'}")
            print(f"   Model: {settings.specific_model_name or 'default'}")
            print(f"   Language: {settings.language or 'english'}")
        else:
            print(f"\n3. AI SETTINGS")
            print(f"   WARNING: No bot settings found")

        # Check integration
        integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
        if integ:
            print(f"\n4. INTEGRATION")
            print(f"   Business Type: {integ.business_type or 'product'}")
            print(f"   WooCommerce URL: {integ.woocommerce_url or 'Not set'}")
            print(f"   WordPress URL: {integ.wp_base_url or 'Not set'}")

            website_url = integ.woocommerce_url or integ.wp_base_url
            if not website_url:
                print(f"   WARNING: No website URL configured!")
                print(f"   ACTION: Add your website URL in Integration settings")
        else:
            print(f"\n4. INTEGRATION")
            print(f"   ERROR: No integration found")
            return

        # Check cached data
        cache = db.query(SiteInfoCache).filter(SiteInfoCache.bot_id == bot.id).first()
        print(f"\n5. WEBSITE DATA CACHE")
        if cache:
            print(f"   Status: CACHED")
            print(f"   Site Name: {cache.site_name}")
            print(f"   Services: {len(cache.services) if cache.services else 0} items")
            print(f"   Phone: {cache.phone or 'Not found'}")
            print(f"   Email: {cache.email or 'Not found'}")
            print(f"   Address: {cache.address[:50] if cache.address else 'Not found'}...")
            print(f"   Products: {len(cache.products) if cache.products else 0} items")
            print(f"   Last Updated: {cache.last_updated}")

            # Check if data is meaningful
            has_data = (
                bool(cache.phone) or
                bool(cache.email) or
                (cache.services and len(cache.services) > 0) or
                (cache.products and len(cache.products) > 0)
            )

            if not has_data:
                print(f"   WARNING: Cache exists but contains no meaningful data")
                print(f"   ACTION: Try fetching website content again")
        else:
            print(f"   Status: NOT CACHED")
            print(f"   WARNING: No website data cached!")
            print(f"   ACTION: Go to Integration page and click 'Fetch Website Content'")

        # Summary
        print(f"\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        issues = []
        if bot.mode != "ai":
            issues.append("Bot is not in AI mode")
        if not settings or not settings.api_key:
            issues.append("No API key configured")
        if not (integ.woocommerce_url or integ.wp_base_url):
            issues.append("No website URL configured")
        if not cache:
            issues.append("No website data cached")
        elif cache and not (cache.phone or cache.email or (cache.services and len(cache.services) > 0)):
            issues.append("Cached data is empty or incomplete")

        if issues:
            print(f"\nFOUND {len(issues)} ISSUE(S):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")

            print(f"\nTO FIX:")
            print(f"   1. Go to Integration page")
            print(f"   2. Add your website URL")
            print(f"   3. Click 'Fetch Website Content' button")
            print(f"   4. Go to Bot Engine page")
            print(f"   5. Set Mode to 'AI'")
            print(f"   6. Add your OpenRouter/OpenAI API key")
            print(f"   7. Save settings")
            print(f"   8. Test by sending a WhatsApp message")
        else:
            print(f"\nALL CHECKS PASSED!")
            print(f"AI mode should be working correctly.")
            print(f"Test by sending: 'What is your phone number?'")

    finally:
        db.close()

if __name__ == "__main__":
    check_ai_mode_setup()
