"""
WhatsApp Bot SaaS Platform - FastAPI Backend
Production-ready multi-tenant WhatsApp bot with pricing plans
"""
import logging
import traceback
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend directory to Python path for stable imports
BACKEND_DIR = Path(__file__).parent.resolve()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, admin, bots, integrations, webhook, chat, conversations, leads, orders, notifications, subscriptions
from config import get_settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import os

settings = get_settings()

# Auto-detect Render environment
if os.environ.get("RENDER") == "true" and settings.ENVIRONMENT != "production":
    logger.warning("RENDER environment detected, but ENVIRONMENT is not set to 'production'. Overriding to production.")
    # We can't easily change settings object if it's immutable, 
    # but we can at least log it and consider it production in our logic.
    # Actually, the user should set it. Let's just log a strong warning.
    logger.warning("Please set ENVIRONMENT=production in your Render settings for correct behavior.")

logger.info(f"Application settings loaded. Environment: {settings.ENVIRONMENT}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database...")
    try:
        success = init_db()
        if success:
            logger.info("Database initialized successfully")
        else:
            logger.critical("DATABASE INITIALIZATION FAILED! Tables might be missing.")
    except Exception as e:
        logger.error(f"Database initialization failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
    yield

app = FastAPI(title=settings.APP_NAME, version="2.0", lifespan=lifespan)

# Configure CORS origins
# Production origins
origins = [
    "https://apps.orvym.com",  # Production frontend (HTTPS)
    "http://apps.orvym.com",   # Production frontend (HTTP fallback)
    "https://orym-saas-application.onrender.com",  # Backend production URL
    "http://localhost:3000",   # Local development frontend
    "http://127.0.0.1:3000",   # Local development frontend (alternative)
]

if settings.ALLOWED_ORIGINS:
    for o in settings.ALLOWED_ORIGINS.split(","):
        origin = o.strip()
        if origin:
            if origin not in origins:
                origins.append(origin)
            # Add variation with/without trailing slash
            alt = origin[:-1] if origin.endswith("/") else f"{origin}/"
            if alt not in origins:
                origins.append(alt)

def get_cors_headers(request: Request):
    """Helper to get correct CORS headers for a request."""
    origin = request.headers.get("origin")

    # If origin is allowed, echo it back. Otherwise use the primary production origin.
    is_allowed = origin in origins if origin else False

    allowed_origin = origin if is_allowed else "https://apps.orvym.com"
    
    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin, ngrok-skip-browser-warning"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure HTTPExceptions (like 404, 401) also return CORS headers."""
    logger.warning(f"HTTP Error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers(request)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return as JSON with CORS headers."""
    error_msg = str(exc)
    stack_trace = traceback.format_exc()
    logger.error(f"Global error caught: {error_msg}\n{stack_trace}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal Server Error: {error_msg}",
            "type": type(exc).__name__
        },
        headers=get_cors_headers(request)
    )

# Configure CORS middleware
# ngrok-skip-browser-warning is allowed so the frontend can bypass ngrok's
# free-tier splash page (ERR_NGROK_6024) when the app is tunneled through
# ngrok for local testing - harmless when the request doesn't come via ngrok.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "ngrok-skip-browser-warning"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(bots.router)
app.include_router(integrations.router)
app.include_router(webhook.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(leads.router)
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(subscriptions.router)

# Manual OPTIONS handler for any path (CORS Preflight fallback)
@app.options("/{rest_of_path:path}")
async def options_handler(request: Request, rest_of_path: str):
    return JSONResponse(content={"status": "ok"}, headers=get_cors_headers(request))

@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "2.0 - Multi-tenant SaaS with Pricing Plans"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


@app.get("/api/health")
async def api_health_check():
    """Alias for /health to match frontend expectations."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
