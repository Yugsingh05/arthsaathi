from __future__ import annotations

from pydantic import BaseModel, Field


class ConsentUpdate(BaseModel):
    purpose: str = Field(..., description="personalisation | stress_watch | fraud_watch")
    granted: bool


class AssistantStart(BaseModel):
    customer_id: str
    flow: str = Field("loan", description="loan | onboarding")
    lang: str = "en"
    as_of: str | None = None


class AssistantReply(BaseModel):
    session_id: str
    text: str


class InterventionRequest(BaseModel):
    customer_id: str
    action: str = Field(..., description="emi_holiday | restructure | call_back | confirm_fraud | release_hold")
    as_of: str | None = None


class OverrideRequest(BaseModel):
    customer_id: str
    decision: str = Field(..., description="uphold | override")
    note: str = ""
    officer: str = "demo.officer"
