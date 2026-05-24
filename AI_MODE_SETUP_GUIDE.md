# AI Mode Setup & Troubleshooting Guide

## Overview
This guide explains how to properly configure AI mode so your WhatsApp bot can answer questions using your website content.

---

## Prerequisites

1. **Website URL**: Your business website (e.g., https://example.com)
2. **API Key**: OpenRouter or OpenAI API key
3. **WhatsApp Integration**: Phone number and token configured

---

## Setup Steps

### 1️⃣ Configure Website Integration

**Location**: Integration Page → Platform Tab

1. Add your website URL:
   - **Product/E-commerce business**: Enter in "WooCommerce URL" field
   - **Service business**: Enter in "WordPress URL" field
   
2. Click **Save**

3. Click **"Fetch Website Content"** button

4. Wait for success message showing:
   - ✅ Site name detected
   - ✅ Services found
   - ✅ Contact info extracted
   - ✅ Products found (if applicable)

**What this does**: Scrapes your website to extract business information, services, contact details, and products. This data is cached and provided to the AI.

---

### 2️⃣ Configure AI Settings

**Location**: Bot Engine Page

1. **Mode**: Change from "Default" to **"AI"**

2. **API Key**: Add your API key
   - OpenRouter: https://openrouter.ai/keys
   - OpenAI: https://platform.openai.com/api-keys
   - Gemini: https://aistudio.google.com/app/apikey

3. **Provider**: Select your AI provider
   - OpenRouter (recommended - access to multiple models)
   - OpenAI (GPT-4, GPT-4o)
   - Gemini (Google's models)

4. **Model**: Choose specific model (optional)
   - OpenRouter: `openai/gpt-4o-mini` (fast & cheap)
   - OpenAI: `gpt-4o-mini`
   - Gemini: `gemini-2.0-flash`

5. **Custom Prompt** (optional): Add instructions for AI behavior
   - Example: "You are a friendly sales assistant. Always be helpful and professional."

6. Click **Save**

---

### 3️⃣ Test AI Mode

Send these test messages to your WhatsApp bot:

1. **Contact Info Test**:
   - "What is your phone number?"
   - "What is your email?"
   - "Where are you located?"

2. **Services Test**:
   - "What services do you offer?"
   - "Tell me about your business"

3. **Products Test** (if applicable):
   - "What products do you have?"
   - "Show me your catalog"

**Expected Behavior**: AI should respond with actual information from your website, not generic responses.

---

## Troubleshooting

### Issue: AI says "I don't have that information"

**Cause**: Website data not cached or empty

**Fix**:
1. Go to Integration page
2. Click "Fetch Website Content" again
3. Check that success message shows actual data (not just "0 services, 0 products")
4. If still empty, your website might not have structured data - try a different URL or add content manually

---

### Issue: AI not responding at all

**Cause**: API key invalid or bot not in AI mode

**Fix**:
1. Verify bot mode is set to "AI" (not "Default" or "Predefined")
2. Check API key is correct and has credits
3. Check logs for error messages

---

### Issue: AI responds but with wrong information

**Cause**: Old cached data or AI hallucinating

**Fix**:
1. Re-fetch website content to update cache
2. Add a custom prompt instructing AI to only use provided data
3. Check that your website actually contains the information

---

## How It Works

### Data Flow

```
Website → Fetch Content → Cache → AI Context → AI Response → User
```

1. **Fetch**: System scrapes your website for:
   - Site name and description
   - Services offered
   - Contact info (phone, email, address, hours)
   - Products (if e-commerce)

2. **Cache**: Data stored in database for 24 hours

3. **AI Context**: When user sends message, cached data is included in AI prompt

4. **AI Response**: AI uses provided data to answer questions

### What AI Receives

The AI gets a structured prompt with:

```
## ABOUT [Your Business]
Description: [Your site description]
About Us: [About page content]

## OUR SERVICES
1. Service 1
2. Service 2
...

## CONTACT INFORMATION
- Phone: [Your phone]
- Email: [Your email]
- Address: [Your address]
- Hours: [Business hours]

## PRODUCT CATALOG (if applicable)
- Product 1 | Price | Stock status
- Product 2 | Price | Stock status
...
```

The AI is instructed to:
- ✅ Use ONLY the information provided above
- ✅ Share contact details when asked
- ✅ List services/products from the data
- ❌ NEVER say "visit the website"
- ❌ NEVER make up information

---

## Diagnostic Tool

Run this command to check your setup:

```bash
cd backend
python test_ai_mode.py
```

This will show:
- ✅ Bot mode (should be "ai")
- ✅ API key status
- ✅ Website URL configured
- ✅ Cached data status
- ✅ What data is available

---

## Best Practices

### 1. Keep Website Data Fresh
- Re-fetch content when you update your website
- Cache expires after 24 hours automatically

### 2. Write Clear Custom Prompts
Good prompt:
```
You are a helpful assistant for [Business Name]. 
Answer questions using the information provided below.
Be friendly and professional.
```

Bad prompt:
```
Be the best AI ever and know everything!
```

### 3. Test Regularly
- Test after any configuration change
- Test with different question types
- Monitor AI responses for accuracy

### 4. Monitor API Usage
- Check your API provider dashboard
- Set up usage alerts
- Use cheaper models for testing (gpt-4o-mini, gemini-flash)

---

## Code Improvements Made

### 1. Enhanced AI Prompt Structure
- Clearer section headers (CONTACT, SERVICES, PRODUCTS)
- Step-by-step instructions for AI
- Explicit rules about what to do/not do

### 2. Better Data Validation
- Checks if meaningful data exists before sending to AI
- Logs what data is being passed
- Fallback handling for missing data

### 3. Improved Logging
- Tracks data flow from cache to AI
- Shows what information AI receives
- Helps diagnose issues

### 4. Contact Info Handling
- Shows actual contact details when available
- Indicates when info is being updated
- No more "Available on website" placeholders

---

## Support

If you're still having issues:

1. Check the diagnostic output: `python test_ai_mode.py`
2. Review application logs for errors
3. Verify your website has the information you expect
4. Test with a simple question first: "What is your phone number?"

---

## Quick Reference

| Setting | Location | Required |
|---------|----------|----------|
| Website URL | Integration → Platform | ✅ Yes |
| Fetch Content | Integration → Button | ✅ Yes |
| Bot Mode | Bot Engine → Mode | ✅ Yes (set to "AI") |
| API Key | Bot Engine → API Key | ✅ Yes |
| Provider | Bot Engine → Provider | ✅ Yes |
| Model | Bot Engine → Model | Optional |
| Custom Prompt | Bot Engine → Prompt | Optional |

---

Last Updated: 2026-05-24
