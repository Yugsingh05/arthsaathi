from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.engine import get_engine

app = FastAPI(title="ArthSaathi", version="0.1.0",
              description="AI-powered hyper-personalized banking layer for Bharat")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.on_event("startup")
def warm() -> None:
    get_engine()


@app.get("/health")
def health() -> dict:
    return {"ok": True}
