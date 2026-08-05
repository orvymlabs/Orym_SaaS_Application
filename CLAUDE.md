# CLAUDE.md

## Project Context

This project is a WhatsApp SaaS platform with Meta WhatsApp Business integration.

The application is already connected to a published Meta App and an existing WhatsApp bot is working in production.

DO NOT break, remove, reset, or replace the existing WhatsApp bot configuration.

The current task is to make Meta WhatsApp Embedded Signup work correctly during LOCAL DEVELOPMENT.

---

# Current Architecture

## Frontend

- Framework: Next.js
- Local port: `3000`
- Local URL:
  `http://localhost:3000`

Important page:

`/dashboard/integrations`

Local page:

`http://localhost:3000/dashboard/integrations`

---

## Backend

- Backend runs locally on port `8001`
- Backend is exposed through ngrok for Meta webhooks.

Current backend ngrok URL:

`https://expulsive-unoperating-cordie.ngrok-free.dev`

Backend webhook URL depends on the actual route implemented in the code.

DO NOT assume `/webhook` or `/api/webhook`.

Inspect the backend routes and use the actual implemented webhook endpoint.

---

# Meta Embedded Signup Requirement

The application needs Meta WhatsApp Embedded Signup.

The OAuth redirect must point to the FRONTEND, not directly to the backend.

The backend ngrok URL is for Meta webhooks only.

Do NOT use:

`http://localhost:3000/dashboard/integrations`

as the production OAuth redirect while Meta HTTPS enforcement is enabled.

For local testing, expose the frontend using a second HTTPS ngrok tunnel.

Run:

`ngrok http 3000`

This produces a URL similar to:

`https://example.ngrok-free.dev`

The actual URL is dynamic and MUST NOT be hardcoded permanently.

---

# Local Development Architecture

Expected architecture:

META
  |
  | Embedded Signup / OAuth
  |
  v
FRONTEND NGROK
https://<frontend-ngrok-domain>
  |
  v
Next.js
localhost:3000
  |
  v
Backend
localhost:8001
  |
  v
BACKEND NGROK
https://expulsive-unoperating-cordie.ngrok-free.dev
  |
  | Webhook
  v
META

---

# OAuth Redirect URI

The OAuth redirect URI must be:

`https://<FRONTEND_NGROK_DOMAIN>/dashboard/integrations`

Example:

`https://abc123.ngrok-free.dev/dashboard/integrations`

DO NOT use the backend ngrok domain as the OAuth redirect.

DO NOT use:

`http://localhost:3000/dashboard/integrations`

when Meta requires HTTPS.

DO NOT hardcode an example ngrok domain.

---

# Meta Configuration

The following values need to correspond to the actual current frontend ngrok URL.

## App Domains

Add:

`<FRONTEND_NGROK_DOMAIN>`

Example:

`abc123.ngrok-free.dev`

Keep existing required domains if they are already being used by the application.

Do not remove existing production domains.

---

## Valid OAuth Redirect URIs

Add:

`https://<FRONTEND_NGROK_DOMAIN>/dashboard/integrations`

Example:

`https://abc123.ngrok-free.dev/dashboard/integrations`

The URI must match the application redirect URI EXACTLY.

Check:

- HTTPS
- Domain
- Port
- Path
- Trailing slash
- Case

Do not introduce mismatches.

---

## Allowed Domains for the JavaScript SDK

Add:

`<FRONTEND_NGROK_DOMAIN>`

Example:

`abc123.ngrok-free.dev`

Do not include:

`https://`

in the Allowed Domains value unless Meta specifically requires it.

---

# Backend Webhook

The backend ngrok URL is used for Meta webhook communication.

Current backend ngrok base:

`https://expulsive-unoperating-cordie.ngrok-free.dev`

Before configuring Meta, inspect the backend source code and determine the actual webhook route.

Possible examples:

`/webhook`

or:

`/api/webhook`

Do NOT guess the route.

Use the route actually implemented by the backend.

Final webhook should therefore be:

`https://expulsive-unoperating-cordie.ngrok-free.dev/<ACTUAL_WEBHOOK_ROUTE>`

---

# Critical Rules

## 1. Do not break the existing WhatsApp bot

The existing bot is already working.

DO NOT:

- Create a new Meta App
- Delete the existing Meta App
- Unpublish the Meta App
- Remove the existing WhatsApp phone number
- Reset WhatsApp configuration
- Replace the existing webhook unnecessarily
- Change working production credentials
- Disconnect the current WhatsApp Business Account
- Modify unrelated WhatsApp settings

Only make changes required for Embedded Signup/local testing.

---

## 2. Do not hardcode temporary ngrok URLs

Ngrok URLs can change.

Never permanently hardcode:

`https://abc123.ngrok-free.dev`

into application logic.

Use environment variables where appropriate.

Example:

`NEXT_PUBLIC_APP_URL`

or an equivalent existing environment variable.

For local development, the current frontend ngrok URL can be supplied through `.env.local`.

Example:

`NEXT_PUBLIC_APP_URL=https://<CURRENT_FRONTEND_NGROK_DOMAIN>`

Do not commit secrets or temporary environment values to Git.

---

# OAuth Flow

Expected flow:

1. User opens the local dashboard.
2. User goes to `/dashboard/integrations`.
3. User clicks Connect WhatsApp.
4. Meta Embedded Signup opens.
5. User completes Meta onboarding.
6. Meta redirects to:

`https://<FRONTEND_NGROK_DOMAIN>/dashboard/integrations`

7. Frontend receives/processes the OAuth result according to the existing implementation.
8. Backend handles required API calls.
9. Meta sends webhooks to the backend ngrok URL.
10. Existing bot functionality remains intact.

---

# Debugging Instructions

Before changing code, inspect the existing implementation.

Find:

- Embedded Signup initialization
- Facebook Login / OAuth configuration
- `redirect_uri`
- Meta SDK initialization
- OAuth callback handling
- WhatsApp Embedded Signup callback
- Webhook routes
- Environment variables
- Existing WhatsApp credentials/configuration

Search the project for:

`redirect_uri`

`facebook`

`oauth`

`embedded signup`

`whatsapp`

`FB.login`

`config_id`

`webhook`

`META`

`WHATSAPP`

---

# Important: Do Not Guess

If a configuration value already exists in the project, inspect and reuse it.

Do not invent:

- Meta App ID
- Meta Config ID
- OAuth redirect URI
- Webhook route
- Verify token
- Access token
- Phone Number ID
- Business Account ID

Use the values already configured in the project/environment.

Never expose secrets in source code.

---

# Environment Variables

Check `.env`, `.env.local`, and backend environment configuration before making changes.

Use environment variables for:

- Meta App ID
- Meta App Secret
- Facebook Login configuration ID
- WhatsApp credentials
- Verify token
- Backend URL
- Frontend URL
- OAuth redirect URI

Never commit secrets.

Never print access tokens or app secrets in logs.

---

# Frontend and Backend Separation

Remember:

Frontend:

`localhost:3000`

Frontend public tunnel:

`https://<frontend-ngrok-domain>`

Backend:

`localhost:8001`

Backend public tunnel:

`https://expulsive-unoperating-cordie.ngrok-free.dev`

OAuth Redirect:

`https://<frontend-ngrok-domain>/dashboard/integrations`

Webhook:

`https://expulsive-unoperating-cordie.ngrok-free.dev/<actual-webhook-route>`

OAuth redirect and webhook URL are NOT the same thing.

---

# Current Problem To Solve

The current Meta Embedded Signup error says the OAuth redirect URI is invalid.

The problematic URI is:

`http://localhost:3000/dashboard/integrations`

The solution for local HTTPS testing is:

1. Keep Next.js running on port `3000`.
2. Start a second ngrok tunnel:

`ngrok http 3000`

3. Get the actual frontend HTTPS ngrok URL.
4. Configure Meta's Valid OAuth Redirect URI using:

`https://<frontend-ngrok-domain>/dashboard/integrations`

5. Configure Allowed Domains using:

`<frontend-ngrok-domain>`

6. Keep the existing backend ngrok tunnel for webhooks.
7. Test Embedded Signup.
8. Verify that the existing WhatsApp bot still works.

---

# Before Making Changes

First inspect the project and explain:

1. Where Embedded Signup is implemented.
2. What redirect URI is currently being generated.
3. What Meta configuration ID is being used.
4. What backend webhook route actually exists.
5. Which environment variables control the frontend/backend URLs.
6. Whether the current implementation already supports a configurable public frontend URL.

Only then modify the minimum required files.

---

# Success Criteria

The task is successful when:

- Local Next.js app runs on port `3000`.
- Backend runs on port `8001`.
- Frontend has an HTTPS ngrok URL.
- Meta accepts the OAuth redirect URI.
- Embedded Signup opens successfully.
- Meta redirects back to `/dashboard/integrations`.
- Backend receives Meta webhooks through its ngrok URL.
- Existing WhatsApp bot continues working.
- No production Meta configuration is unnecessarily changed.
- No secrets are exposed or committed.
- Temporary ngrok URLs are not permanently hardcoded.

---

# Final Instruction

Be conservative with changes.

This is an existing working WhatsApp SaaS application.

Do not rewrite the WhatsApp integration.

Do not replace working code unnecessarily.

Inspect first, identify the exact cause, then make the smallest safe change required to enable Meta Embedded Signup local testing.