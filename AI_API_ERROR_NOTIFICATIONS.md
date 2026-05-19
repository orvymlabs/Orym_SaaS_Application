# AI API Error Notifications - Implementation

**Date**: 2026-05-14  
**Status**: ✅ COMPLETED

---

## Overview

This feature creates **dashboard notifications** when the user's external AI API (OpenAI, OpenRouter, Gemini, Qwen) encounters errors like rate limits, quota exceeded, or invalid API keys.

---

## Problem Solved

**Before**: When user's AI API key had issues (rate limit, quota exceeded, invalid key), the bot would silently fail and users wouldn't know why AI mode stopped working.

**After**: Users receive immediate notifications in their dashboard when their AI API encounters errors, with clear explanations and action steps.

---

## Error Types Detected

### 1. Rate Limit Exceeded (HTTP 429)
**When**: User's API provider rate limit is hit (too many requests per minute/hour)

**Notification**:
- **Title**: "AI API Rate Limit Exceeded"
- **Message**: "Your [PROVIDER] API rate limit has been exceeded. Please wait a few minutes or check your API provider dashboard."

**User Action**: Wait a few minutes, or upgrade API plan

---

### 2. Quota/Credits Exceeded (HTTP 402, 403)
**When**: User's API credits/quota are exhausted

**Notification**:
- **Title**: "AI API Quota Exceeded"
- **Message**: "Your [PROVIDER] API quota/credits have been exhausted. Please add credits to your API provider account or upgrade your plan."

**User Action**: Add credits to OpenAI/OpenRouter/etc. account

---

### 3. Invalid API Key (HTTP 401)
**When**: API key is invalid, expired, or revoked

**Notification**:
- **Title**: "Invalid AI API Key"
- **Message**: "Your [PROVIDER] API key is invalid or has been revoked. Please update your API key in Bot Engine settings."

**User Action**: Update API key in Dashboard → Bot Engine

---

### 4. API Timeout
**When**: API request takes too long (>12 seconds)

**Notification**:
- **Title**: "AI API Timeout"
- **Message**: "The [PROVIDER] API request timed out. This may be temporary - please try again."

**User Action**: Usually temporary, no action needed

---

## How It Works

### Flow Diagram

```
WhatsApp Message → Bot Engine (AI Mode)
                    ↓
                Check Platform Limit (our limit)
                    ↓
                Call External AI API (OpenAI/OpenRouter/etc.)
                    ↓
                ┌─────────────────┐
                │ API Response?   │
                └─────────────────┘
                    ↓
        ┌───────────┴───────────┐
        │                       │
    Success                  Error
        │                       │
    Return AI                   ├─ 429 → Rate Limit
    Response                    ├─ 402/403 → Quota Exceeded
        │                       ├─ 401 → Invalid Key
        │                       └─ Timeout → API Timeout
        │                           ↓
        │                   Create Dashboard Notification
        │                           ↓
        │                   Fallback to Keyword Mode
        │                           ↓
        └───────────────────────────┘
                    ↓
            Send WhatsApp Reply
```

---

## Implementation Details

### Files Modified

#### 1. `backend/services/ai_service.py` (lines 302-327)

**Added error detection**:
```python
if r.status_code == 429:
    return "API_RATE_LIMIT_EXCEEDED"
elif r.status_code in [402, 403]:
    return "API_QUOTA_EXCEEDED"
elif r.status_code == 401:
    return "API_INVALID_KEY"
```

**Added timeout handling**:
```python
except requests.exceptions.Timeout:
    return "API_TIMEOUT"
```

---

#### 2. `backend/services/bot_engine.py` (lines 227-280)

**Added notification creation**:
```python
if ai_resp and ai_resp.startswith("API_"):
    # Create dashboard notification
    error_messages = {
        "API_RATE_LIMIT_EXCEEDED": {...},
        "API_QUOTA_EXCEEDED": {...},
        "API_INVALID_KEY": {...},
        "API_TIMEOUT": {...}
    }
    
    create_notification(
        db=db,
        user_id=user_id,
        type="ai_api_error",
        title=error_info["title"],
        message=error_info["message"]
    )
    
    # Fallback to keyword mode
    return _fallback_to_predefined(...)
```

---

## User Experience

### Dashboard Notification

When AI API error occurs:

1. **Notification Bell Icon** shows new notification
2. User clicks notification dropdown
3. Sees notification with:
   - Clear title (e.g., "AI API Quota Exceeded")
   - Detailed message explaining the issue
   - Action steps to resolve

### WhatsApp Behavior

When AI API error occurs:

1. Bot automatically falls back to **keyword/predefined mode**
2. Customer receives response based on custom keywords
3. **No service interruption** - bot continues working
4. No error message shown to WhatsApp customer

---

## Notification Types

### Database Schema

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    type TEXT,  -- "ai_api_error"
    title TEXT,
    message TEXT,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

### Notification Type: `ai_api_error`

**Purpose**: Alert user about external AI API issues

**Triggers**:
- Rate limit exceeded (429)
- Quota/credits exhausted (402, 403)
- Invalid API key (401)
- API timeout

**Visibility**: Dashboard notification bell icon

---

## Testing Scenarios

### Test 1: Rate Limit
1. Use OpenRouter free tier with low rate limit
2. Send multiple WhatsApp messages quickly
3. Check dashboard for "Rate Limit Exceeded" notification

### Test 2: Invalid API Key
1. Go to Bot Engine settings
2. Enter invalid API key (e.g., "sk_invalid123")
3. Send WhatsApp message
4. Check dashboard for "Invalid API Key" notification

### Test 3: Quota Exceeded
1. Use OpenAI API with $0 balance
2. Send WhatsApp message
3. Check dashboard for "Quota Exceeded" notification

---

## Benefits

✅ **Immediate Awareness**: Users know instantly when their AI API has issues  
✅ **Clear Action Steps**: Notifications explain exactly what to do  
✅ **No Service Interruption**: Bot falls back to keyword mode automatically  
✅ **Better UX**: Users don't wonder why AI stopped working  
✅ **Proactive Monitoring**: Users can fix issues before customers notice  
✅ **Provider-Specific**: Shows which provider (OpenAI, OpenRouter, etc.) has the issue  

---

## Difference from Platform Limit

### Platform Limit (Our Limit)
- **What**: Our platform's AI usage limit (e.g., 500 requests/month)
- **Notification**: "AI Limit Reached - Upgrade your plan"
- **Cause**: User exceeded their plan's AI request quota
- **Solution**: Upgrade to higher plan

### API Limit (External Provider)
- **What**: External AI provider's limit (OpenAI, OpenRouter, etc.)
- **Notification**: "AI API Rate Limit Exceeded" or "AI API Quota Exceeded"
- **Cause**: User's API key hit provider's rate/quota limit
- **Solution**: Wait (rate limit) or add credits (quota)

---

## Error Handling Flow

```
User sends WhatsApp message
    ↓
Bot checks PLATFORM limit (our limit)
    ↓
    ├─ Exceeded? → Notification: "AI Limit Reached"
    │              Fallback to keyword mode
    │
    └─ OK? → Call external AI API
              ↓
              Check API response
              ↓
              ├─ 429/402/403/401? → Notification: "AI API [Error Type]"
              │                      Fallback to keyword mode
              │
              └─ 200 OK? → Return AI response
                           Increment usage counter
```

---

## Configuration

### No Configuration Needed

This feature works automatically for all users with AI mode enabled.

### Requirements

- User must have AI mode enabled
- User must have API key configured
- User must have valid WhatsApp integration

---

## Monitoring

### Logs

All AI API errors are logged:

```
logger.error(f"AI ({provider}) RATE LIMIT EXCEEDED: {r.text}")
logger.error(f"AI ({provider}) QUOTA EXCEEDED: {r.status_code}")
logger.error(f"AI ({provider}) INVALID API KEY: {r.text}")
logger.info(f"Created AI API error notification for user {user_id}")
```

### Notification History

Users can see all past notifications in dashboard notification dropdown.

---

## Future Enhancements

Possible improvements:

1. **Email Notifications**: Send email when critical API errors occur
2. **Retry Logic**: Automatically retry after rate limit cooldown
3. **API Health Dashboard**: Show API status and usage stats
4. **Multiple API Keys**: Fallback to secondary key if primary fails
5. **Cost Tracking**: Track API costs per user

---

## Conclusion

✅ **Implemented**: AI API error notifications  
✅ **Tested**: Error detection and notification creation  
✅ **User-Friendly**: Clear messages with action steps  
✅ **No Interruption**: Automatic fallback to keyword mode  
✅ **Production-Ready**: Fully functional and tested  

Users now receive immediate dashboard notifications when their external AI API (OpenAI, OpenRouter, Gemini, Qwen) encounters errors, with clear explanations and action steps.
