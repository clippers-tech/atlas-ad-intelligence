"""FastAPI application init, router includes, startup/shutdown."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import master_router
from app.services.scheduler.engine import (
    start_scheduler,
    stop_scheduler,
    get_scheduler_status,
)

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ATLAS — Autonomous Ad Intelligence System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
        "https://atlas-frontend-5ta3.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("ATLAS backend starting up...")
    start_scheduler()
    logger.info("ATLAS scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ATLAS backend shutting down...")
    stop_scheduler()
    logger.info("ATLAS scheduler stopped")


@app.get("/")
async def root():
    return {"name": "ATLAS", "status": "running"}


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Return current scheduler status and next run times."""
    return get_scheduler_status()
