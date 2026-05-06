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
from routers import auth, bots, integrations, webhook, chat, conversations, leads, orders
from config import get_settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

logger.info(f"Application settings loaded. Environment: {settings.ENVIRONMENT}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    yield

app = FastAPI(title=settings.APP_NAME, version="2.0", lifespan=lifespan)

# Configure CORS origins
origins = [
    "https://apps.orvym.com",  # Production frontend (HTTPS)
    "http://apps.orvym.com",   # Production frontend (HTTP fallback)
    "http://localhost:3001",   # Local development (Next.js default port)
    "http://127.0.0.1:3001",   # Local development
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
    # We check for exact match or domain match
    is_allowed = False
    if origin in origins:
        is_allowed = True
    elif origin and ("localhost" in origin or "127.0.0.1" in origin):
        is_allowed = True
        
    allowed_origin = origin if is_allowed else "https://apps.orvym.com"
    
    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin"
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(bots.router)
app.include_router(integrations.router)
app.include_router(webhook.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(leads.router)
app.include_router(orders.router)

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
