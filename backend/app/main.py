"""FastAPI application init, router includes, startup/shutdown."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import master_router

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
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("ATLAS backend starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ATLAS backend shutting down...")


@app.get("/")
async def root():
    return {"name": "ATLAS", "status": "running"}
