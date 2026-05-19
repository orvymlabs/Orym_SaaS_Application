# Production URLs Configuration

**Last Updated**: 2026-05-19

---

## 🌐 Production URLs

### Frontend (Next.js)
- **Production URL**: https://apps.orvym.com
- **Alternative**: https://www.orvym.com
- **Local Development**: http://localhost:3000

### Backend (FastAPI)
- **Production URL**: https://orym-saas-application.onrender.com
- **API Docs**: https://orym-saas-application.onrender.com/docs
- **Local Development**: http://localhost:8001

### Webhook (WhatsApp)
- **Production URL**: https://orym-saas-application.onrender.com/webhook
- **Ngrok (Local Testing)**: https://expulsive-unoperating-cordie.ngrok-free.dev/webhook
- **Local Development**: http://localhost:8001/webhook

### Database
- **Production (PostgreSQL)**: 
  ```
  postgresql://orvyn_ut1d_user:LZ7fz2r7JARnJJq4NN6pxOSy10myF4g5@dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com/orvyn_ut1d
  ```
- **Local Development (SQLite)**: `backend/data/saas_bot.db`

---

## 📋 Configuration Files

### Backend Configuration

**File**: `backend/.env`

```env
# Production Mode
ENVIRONMENT=production
DEBUG=false

# Production Database
DATABASE_URL=postgresql://orvyn_ut1d_user:...
POSTGRES_URL=postgresql://orvyn_ut1d_user:...

# CORS Origins (All environments)
ALLOWED_ORIGINS=https://orvym.com,https://www.orvym.com,https://apps.orvym.com,https://orym-saas-application.onrender.com,http://localhost:3000,http://127.0.0.1:3000
```

**File**: `backend/main.py`

```python
# CORS Origins (Production + Development)
origins = [
    "https://apps.orvym.com",  # Production frontend
    "http://apps.orvym.com",   # Production frontend (HTTP)
    "https://orym-saas-application.onrender.com",  # Backend production
    "http://localhost:3000",   # Local development
    "http://127.0.0.1:3000",   # Local development
]
```

### Frontend Configuration

**File**: `frontend/.env` (Production - Default)

```env
# Production URLs
NEXT_PUBLIC_API_URL=https://orym-saas-application.onrender.com
NEXT_PUBLIC_WS_URL=wss://orym-saas-application.onrender.com
NEXT_PUBLIC_WEBHOOK_URL=https://orym-saas-application.onrender.com/webhook
NEXT_PUBLIC_ENV=production
```

**File**: `frontend/.env.local` (Local Development - Override)

```env
# Local Development URLs (overrides .env)
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
NEXT_PUBLIC_WEBHOOK_URL=http://localhost:8001/webhook
```

**File**: `frontend/lib/api.ts`

```typescript
// Uses environment variables with production defaults
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://orym-saas-application.onrender.com';
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'wss://orym-saas-application.onrender.com';
const WEBHOOK_BASE = process.env.NEXT_PUBLIC_WEBHOOK_URL || 'https://orym-saas-application.onrender.com/webhook';
```

---

## 🚀 Deployment Instructions

### Production Deployment

1. **Backend (Render.com)**
   - Push code to GitHub
   - Render auto-deploys from `master` branch
   - Environment variables set in Render dashboard
   - URL: https://orym-saas-application.onrender.com

2. **Frontend (Vercel/Netlify)**
   - Deploy to: https://apps.orvym.com
   - Uses `frontend/.env` for production config
   - Build command: `npm run build`
   - Output directory: `.next`

3. **Database (Render PostgreSQL)**
   - Already configured in backend/.env
   - Connection string in `DATABASE_URL` and `POSTGRES_URL`

### Local Development

1. **Backend**
   ```bash
   cd backend
   # Edit .env to use SQLite (comment out PostgreSQL URLs)
   python main.py
   # Runs on http://localhost:8001
   ```

2. **Frontend**
   ```bash
   cd frontend
   # Create/edit .env.local with local URLs
   npm run dev
   # Runs on http://localhost:3000
   ```

3. **Ngrok (Webhook Testing)**
   ```bash
   ngrok http 8001
   # Use generated URL for WhatsApp webhook
   ```

---

## 🔧 WhatsApp Configuration

### Meta Developer Dashboard

**Webhook URL**: https://orym-saas-application.onrender.com/webhook

**Verify Token**: `whatsapp_bot_verify_token_123` (from backend/.env)

**Webhook Fields to Subscribe**:
- messages
- message_status (optional)

**App Secret**: Set in `backend/.env` as `META_APP_SECRET`

---

## 🔐 Security Notes

1. **Production Secrets**:
   - `SECRET_KEY`: JWT signing key (32+ characters)
   - `ENCRYPTION_KEY`: API key encryption (32 bytes)
   - `META_APP_SECRET`: WhatsApp webhook signature validation
   - `STRIPE_SECRET_KEY`: Payment processing

2. **CORS Configuration**:
   - Production frontend: `https://apps.orvym.com`
   - Backend: `https://orym-saas-application.onrender.com`
   - Local development: `http://localhost:3000` and `http://localhost:8001`

3. **Database**:
   - Production: PostgreSQL (encrypted connection)
   - Local: SQLite (file-based)

---

## 📊 Environment Summary

| Environment | Frontend | Backend | Database | Webhook |
|-------------|----------|---------|----------|---------|
| **Production** | https://apps.orvym.com | https://orym-saas-application.onrender.com | PostgreSQL (Render) | https://orym-saas-application.onrender.com/webhook |
| **Local Dev** | http://localhost:3000 | http://localhost:8001 | SQLite | http://localhost:8001/webhook or Ngrok |
| **Testing** | http://localhost:3000 | http://localhost:8001 | SQLite | Ngrok URL |

---

## ✅ Verification Checklist

- [x] Backend CORS includes all production origins
- [x] Frontend .env uses production URLs by default
- [x] Frontend .env.local overrides for local development
- [x] Backend .env uses PostgreSQL for production
- [x] Backend main.py includes all CORS origins
- [x] Webhook URL configured for production
- [x] Database connection strings updated
- [x] Environment set to production mode

---

## 🆘 Troubleshooting

### CORS Errors
- Check `backend/.env` ALLOWED_ORIGINS includes your frontend URL
- Check `backend/main.py` origins list includes your frontend URL
- Verify no trailing slashes in URLs

### Webhook Not Working
- Verify webhook URL in Meta Developer Dashboard
- Check `META_APP_SECRET` in backend/.env matches Meta dashboard
- Test with ngrok for local development

### Database Connection Issues
- Production: Verify PostgreSQL connection string in backend/.env
- Local: Ensure SQLite file path is accessible (backend/data/)

### API Connection Failed
- Check frontend .env has correct NEXT_PUBLIC_API_URL
- Verify backend is running and accessible
- Check CORS configuration

---

**Note**: For local development, always use `.env.local` to override production settings. Never commit `.env.local` to version control.
