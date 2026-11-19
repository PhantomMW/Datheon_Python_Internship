import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class InboundEmail(BaseModel):
    message_id: str = Field(..., description="Unique message ID or Gmail message ID")
    thread_id: Optional[str] = Field(default=None, description="Thread ID if part of an existing conversation")
    sender_email: str = Field(..., description="Sender email address")
    sender_name: Optional[str] = Field(default="Customer", description="Sender's display name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Raw or plain text email body content")
    received_at: Optional[str] = Field(default=None, description="ISO timestamp")

    @field_validator("sender_email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError(f"Invalid email address format: {v}")
        return v


class SentimentAnalysis(BaseModel):
    sentiment: str = Field(..., description="POSITIVE, NEUTRAL, FRUSTRATED, or ANGRY")
    polarity_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1.0 (very negative) to 1.0 (very positive)")
    urgency_level: str = Field(..., description="HIGH, MEDIUM, or LOW")
    escalation_needed: bool = Field(..., description="Whether human manager escalation is required")


class IntentClassification(BaseModel):
    primary_intent: str = Field(
        ...,
        description="BILLING_QUERY, URGENT_OUTAGE, TECHNICAL_SUPPORT, CANCELLATION_REQUEST, FEATURE_REQUEST, or GENERAL_INQUIRY"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the intent classification")
    secondary_intents: List[str] = Field(default_factory=list)


class KnowledgeArticle(BaseModel):
    id: str
    title: str
    category: str
    content: str
    keywords: List[str]


class DraftReply(BaseModel):
    draft_id: Optional[str] = None
    subject: str
    body_html: str
    body_text: str
    recipient: str


class EmailTriageResult(BaseModel):
    message_id: str
    sender_email: str
    subject: str
    sentiment: SentimentAnalysis
    intent: IntentClassification
    applied_labels: List[str]
    retrieved_knowledge_articles: List[str]
    draft_reply: DraftReply
    processing_time_seconds: float
    status: str = "PROCESSED"
