import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LeadInput(BaseModel):
    full_name: str = Field(..., description="Prospect's full name")
    email: str = Field(..., description="Prospect's business email")
    company_name: str = Field(..., description="Company name")
    company_size: str = Field(..., description="Reported company size or headcount")
    estimated_budget: str = Field(..., description="Estimated project budget")
    project_scope: Optional[str] = Field(default="", description="Description of the project or requirements")
    source: Optional[str] = Field(default="Webhook/Typeform", description="Origin of the lead")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError(f"Invalid email address format: {v}")
        return v


class AIQualificationResult(BaseModel):
    qualification_tier: str = Field(
        ...,
        description="Tier categorization: TIER_1_ENTERPRISE, TIER_2_MID_MARKET, TIER_3_SMB, or UNQUALIFIED"
    )
    score: int = Field(..., ge=0, le=100, description="Lead qualification score between 0 and 100")
    budget_evaluated_usd: float = Field(..., description="Normalized evaluated budget in USD")
    company_size_headcount: int = Field(..., description="Normalized parsed company headcount")
    reasoning: str = Field(..., description="AI reasoning for qualification tier and score")
    urgency: str = Field(..., description="Urgency level: HIGH, MEDIUM, or LOW")
    custom_sales_talking_points: List[str] = Field(
        ...,
        description="Key customized talking points tailored specifically for the sales rep"
    )
    recommended_action: str = Field(
        ...,
        description="Suggested sales action"
    )


class LeadProcessResult(BaseModel):
    lead_id: str
    status: str
    within_sla: bool
    execution_time_seconds: float
    qualification: AIQualificationResult
    airtable_record_id: Optional[str] = None
    slack_alert_sent: bool = False
    message: str
