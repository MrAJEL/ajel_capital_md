"""
AJEL Capital — FastAPI Backend v2.1
=====================================
Security-first: All API keys & external calls happen server-side.
Rate limiting, CORS, security headers — browser never touches secrets.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import os
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.limiter import limiter

from database import engine, Base, get_db
import models.sql_models as sql_models

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ajel-capital")

# ── DB Init ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AJEL Capital API starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables verified/created.")
    yield
    logger.info("👋 AJEL Capital API shutting down.")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AJEL Capital API",
    version="2.1.0",
    description="Secure trading intelligence backend for AJEL Capital",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security Headers Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    # Don't leak server info
    if "server" in response.headers:
        del response.headers["server"]
    return response

# ── CORS — allow frontend (same docker network + localhost dev) ───────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://frontend:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": "AJEL Capital API v2.1", "status": "online"}

@app.get("/api/status", tags=["Health"])
async def get_status(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text # Import here or top level
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        from data.cache import get_redis
        r = get_redis()
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "healthy",
        "database": "connected" if db_ok else "error",
        "redis": "connected" if redis_ok else "unavailable",
        "version": "2.1.0"
    }

# ── Include ALL Routers ──────────────────────────────────────────────────────
from api.auth import router as auth_router
from api.prices import router as prices_router
from api.intelligence import router as intelligence_router
from api.portfolio import router as portfolio_router
from api.clients import router as clients_router

app.include_router(auth_router,         prefix="/api", tags=["Auth"])
app.include_router(prices_router,       prefix="/api", tags=["Market Data"])
app.include_router(intelligence_router, prefix="/api", tags=["Intelligence"])
app.include_router(portfolio_router,    prefix="/api", tags=["Portfolio"])
app.include_router(clients_router,      prefix="/api", tags=["Clients"])

# ── Global Error Handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Never leak internal details in production
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if is_dev else "An unexpected error occurred",
        }
    )
