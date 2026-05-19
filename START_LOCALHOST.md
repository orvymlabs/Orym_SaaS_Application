# Local Development Setup Guide

## Configuration Summary

### Backend (Port 8001)
- **Environment**: Development mode
- **Database**: SQLite (auto-created in `backend/data/saas_bot.db`)
- **CORS**: Configured for localhost:3000
- **Production URLs**: Commented out

### Frontend (Port 3000)
- **API URL**: http://localhost:8001
- **WebSocket URL**: ws://localhost:8001
- **Environment**: Uses `.env.local` for local overrides

---

## Quick Start

### 1. Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

**Test Backend:**
Open http://localhost:8001 in your browser - you should see:
```json
{
  "status": "ok",
  "app": "WhatsApp Bot SaaS",
  "environment": "development"
}
```

### 2. Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
- Local:        http://localhost:3000
- Ready in X ms
```

**Access Dashboard:**
Open http://localhost:3000 in your browser

---

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Windows - Find and kill process on port 8001
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

**Database errors:**
- SQLite database will be auto-created in `backend/data/`
- If issues persist, delete `backend/data/saas_bot.db` and restart

**Module not found:**
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Issues

**Dependencies missing:**
```bash
cd frontend
npm install
```

**API connection failed:**
- Verify backend is running on port 8001
- Check `frontend/.env.local` has correct URLs
- Check browser console for CORS errors

---

## Switching Back to Production

When ready to deploy, revert these changes:

### Backend `.env`
1. Uncomment production DATABASE_URL and POSTGRES_URL
2. Set `ENVIRONMENT=production` and `DEBUG=false`
3. Update ALLOWED_ORIGINS to production domains

### Backend `main.py`
1. Comment out localhost origins
2. Uncomment production origins

### Frontend
Production uses `frontend/.env` (not `.env.local`)

---

## API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## Default Admin Account

If you need to create an admin user:

```bash
cd backend
python create_admin.py
```
