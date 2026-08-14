# Meta Embedded Signup Integration Guide

This guide explains how to implement Meta Embedded Signup for WhatsApp Business API in the Orvym platform.

## Overview

Meta Embedded Signup allows users to connect their WhatsApp Business Account with one click, without manually entering credentials. This significantly improves the onboarding experience.

## Prerequisites

1. A Meta Business Account
2. A Meta App with WhatsApp Business API enabled
3. Your app must be in Live mode (not Development mode)

## Setup Instructions

### Step 1: Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** as the app type
4. Fill in your app details and create the app

### Step 2: Add WhatsApp Product

1. In your app dashboard, click **Add Product**
2. Find **WhatsApp** and click **Set Up**
3. Complete the WhatsApp product setup

### Step 3: Configure Embedded Signup

1. In your app dashboard, go to **WhatsApp** → **Configuration**
2. Scroll down to **Embedded Signup**
3. Click **Create Configuration**
4. Configure the following:
   - **Display Name**: Your app name shown during signup
   - **Callback URL**: `https://your-domain.com/api/integrations/meta/oauth/callback`
   - **Verify Token**: Use the one generated in your integration settings
   - **Webhook Fields**: Select all relevant fields (messages, message_status, etc.)

5. Save the configuration and copy the **Configuration ID**

### Step 4: Get Your App Credentials

1. Go to **Settings** → **Basic**
2. Copy your **App ID**
3. Copy your **App Secret** (click Show to reveal it)

### Step 5: Configure Backend Environment Variables

Add the following to your `backend/.env` file:

```env
# Meta WhatsApp Configuration
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_CONFIG_ID=your_configuration_id_here
```

### Step 6: Configure App Domain

1. In Meta App Dashboard, go to **Settings** → **Basic**
2. Add your domain to **App Domains**:
   - For production: `your-domain.com`
   - For development: `localhost` or your ngrok domain

3. Update **Privacy Policy URL** and **Terms of Service URL**

### Step 7: Set Up Webhooks

1. Go to **WhatsApp** → **Configuration**
2. Under **Webhooks**, click **Edit**
3. Enter your webhook URL: `https://your-domain.com/webhook`
4. Enter the verify token (from your integration settings)
5. Subscribe to the following fields:
   - `messages`
   - `message_status`
   - `message_template_status_update`

### Step 8: Switch to Live Mode

1. Go to **Settings** → **Basic**
2. Toggle **App Mode** from Development to Live
3. Complete the App Review if required by Meta

## How It Works

### User Flow

1. User clicks **Connect WhatsApp** button
2. Facebook login popup appears
3. User logs in with their Facebook account
4. User selects their business
5. User selects their WhatsApp Business Account
6. User selects which phone number to use
7. User grants permissions
8. Meta returns an authorization code
9. Backend exchanges code for access token
10. Credentials are automatically saved to the database

### Backend Flow

```
Frontend                Backend                 Meta API
   |                       |                        |
   |-- Click Connect ----->|                        |
   |                       |                        |
   |<-- Launch FB SDK -----|                        |
   |                       |                        |
   |-- User Authorizes --->|                        |
   |                       |                        |
   |-- Send Code --------->|                        |
   |                       |-- Exchange Code ------>|
   |                       |<-- Access Token -------|
   |                       |                        |
   |                       |-- Get WABA ID -------->|
   |                       |<-- WABA Details -------|
   |                       |                        |
   |                       |-- Get Phone Numbers -->|
   |                       |<-- Phone List ---------|
   |                       |                        |
   |                       |-- Save to Database ----|
   |                       |                        |
   |<-- Success Response --|                        |
```

## API Endpoints

### GET /api/integrations/meta/config

Returns Meta App configuration for frontend.

**Response:**
```json
{
  "app_id": "123456789",
  "config_id": "987654321"
}
```

### POST /api/integrations/meta/oauth/callback

Handles OAuth callback after user authorization.

**Request:**
```json
{
  "code": "authorization_code_from_meta"
}
```

**Response:**
```json
{
  "success": true,
  "message": "WhatsApp connected successfully",
  "data": {
    "business_name": "My Business",
    "phone_number": "+1234567890",
    "phone_number_id": "109876543210"
  }
}
```

### POST /api/integrations/whatsapp/disconnect

Disconnects WhatsApp integration.

**Response:**
```json
{
  "success": true,
  "message": "WhatsApp disconnected successfully"
}
```

## Backward Compatibility

The manual credential entry form is preserved as a fallback:

- If `META_APP_ID` and `META_CONFIG_ID` are not set, users see the manual form
- Existing integrations continue working without changes
- All existing bots, flows, and automations remain functional
- Users can switch between Embedded Signup and manual setup

## Testing

### Development Testing

1. Use ngrok to expose your local backend:
   ```bash
   ngrok http 8001
   ```

2. Update your Meta App settings with the ngrok URL

3. Test the flow:
   - Click "Connect WhatsApp"
   - Complete the authorization
   - Verify credentials are saved correctly

### Production Testing

1. Ensure your domain is properly configured in Meta App settings
2. Verify SSL certificate is valid
3. Test with a real WhatsApp Business Account
4. Verify webhook events are received

## Troubleshooting

### "Meta Embedded Signup is not configured"

**Solution**: Add `META_APP_ID`, `META_APP_SECRET`, and `META_CONFIG_ID` to `backend/.env`

### "Failed to exchange authorization code"

**Possible causes:**
- Invalid App Secret
- Expired authorization code
- Network timeout

**Solution**: Verify your credentials and try again

### "Phone number already connected to another account"

**Cause**: The phone number is already registered with another integration

**Solution**: Disconnect from the other account first, or use a different phone number

### Webhook verification fails

**Cause**: Verify token mismatch

**Solution**: Ensure the verify token in Meta App matches the one in your integration settings

## Security Considerations

1. **Never expose App Secret**: Keep it in backend environment variables only
2. **Use HTTPS**: Meta requires HTTPS for production webhooks
3. **Validate webhook signatures**: The `META_APP_SECRET` is used to verify webhook authenticity
4. **Encrypt tokens**: Access tokens are encrypted before storing in database
5. **Check phone number uniqueness**: System prevents duplicate phone number registrations

## Data Storage

The following data is stored in the `integrations` table:

- `whatsapp_token`: Encrypted access token
- `phone_number_id`: WhatsApp Phone Number ID (unique)
- `whatsapp_number`: Display phone number (for wa.me links)
- `verify_token`: Webhook verification token (alphanumeric only)

## Support

For Meta-related issues:
- [Meta for Developers Documentation](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp/business-management-api)

For Orvym platform issues:
- Check application logs
- Review error messages in browser console
- Verify environment variables are set correctly
