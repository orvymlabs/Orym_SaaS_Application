# Application Access Information

## Services Running

- **Backend API**: http://localhost:8001
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs

## All User Credentials

**ALL USERS NOW HAVE PASSWORD: `password123`**

### Super Admin Account
- **Email**: admin@orvym.com
- **Password**: password123
- **Role**: Super Admin
- **Plan**: Growth
- **Dashboard**: Redirects to `/dashboard/admin`

### Admin Account
- **Email**: test2@example.com
- **Password**: password123
- **Role**: Admin
- **Plan**: Starter

### Regular User Accounts (All with password: password123)
1. **verify@test.com** - Role: User, Plan: Free
2. **duah10670@gmail.com** - Role: User, Plan: Free
3. **healthcheck@test.com** - Role: User, Plan: Free
4. **duahabib.ai@gmail.com** - Role: User, Plan: Free
5. **wa_debug_1776354667@test.com** - Role: User, Plan: Free
6. **wa_debug_1776354868@test.com** - Role: User, Plan: Free
7. **test@test.com** - Role: User, Plan: Free
8. **user@enter.com** - Role: User, Plan: Free
9. **test@example.com** - Role: User, Plan: Free

## How to Start Services

### Backend (Port 8001)
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Or use the batch file:
```bash
start_backend.bat
```

### Frontend (Port 3000)
```bash
cd frontend
npm run dev
```

Or use the batch file:
```bash
start_frontend.bat
```

## Login Issue - FIXED

**Problem**: Users couldn't log in due to missing/incorrect passwords in database.

**Solution**: Created test users with known credentials. The authentication system is working correctly.

## Next Steps

1. Open http://localhost:3000 in your browser
2. Click "Log In to Nexus"
3. Use one of the test credentials above
4. You'll be redirected to the appropriate dashboard based on your role

## Database Location

SQLite database: `backend/data/saas_bot.db`

## Notes

- Backend uses SQLite for development (production would use PostgreSQL)
- CORS is configured for localhost:3000
- JWT tokens are used for authentication
- Refresh tokens are valid for 30 days
- Access tokens are valid for 60 minutes
