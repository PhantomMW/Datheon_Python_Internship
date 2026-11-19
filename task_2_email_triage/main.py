from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from task_2_email_triage.schemas import InboundEmail, EmailTriageResult
from task_2_email_triage.pipeline import EmailTriagePipeline

app = FastAPI(
    title="Datheon AI - Autonomous Support & Intelligent Email Triage API",
    description="Intelligent Gmail triage: sentiment analysis, intent categorization, KB lookup, auto-tagging, and polite draft generation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = EmailTriagePipeline()


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "task_2_email_triage", "capabilities": ["sentiment", "intent", "tagging", "draft_generation"]}


@app.post(
    "/api/v1/triage/process",
    response_model=EmailTriageResult,
    status_code=status.HTTP_200_OK,
    tags=["Email Triage"]
)
async def process_email_endpoint(email: InboundEmail):
    """
    Ingests inbound email, runs sentiment analysis, categorizes intent,
    queries internal knowledge base, applies labels, and drafts polite response.
    """
    return await pipeline.triage_email(email)


@app.get(
    "/api/v1/triage/demo",
    response_model=Dict[str, Any],
    tags=["Demonstration"]
)
async def run_support_demo():
    """Runs autonomous triage across 4 diverse customer scenarios."""
    scenarios = [
        InboundEmail(
            message_id="msg_outage_001",
            sender_name="Marcus Vance",
            sender_email="marcus@enterprise-corp.com",
            subject="CRITICAL: Production API 500 error down during peak traffic",
            body="Hello team, our core webhook receiver has been failing with HTTP 500 errors for the past 20 minutes. We have customers actively impacted. This is urgent, please fix ASAP!",
            received_at="2026-11-19T03:30:00Z"
        ),
        InboundEmail(
            message_id="msg_billing_002",
            sender_name="Chloe Bennett",
            sender_email="chloe.b@startup.io",
            subject="Question regarding double charge on invoice #9401",
            body="Hi there, I reviewed our bank statement and it looks like we were billed twice for this month's subscription. Could you check the transaction and issue a credit?",
            received_at="2026-11-19T03:32:00Z"
        ),
        InboundEmail(
            message_id="msg_cancel_003",
            sender_name="Robert King",
            sender_email="rking@lawpartners.net",
            subject="Extremely disappointed - Need full refund immediately",
            body="Your platform has been totally broken for our use case and your support was unhelpful last week. We signed up 4 days ago. Cancel our plan and issue a full refund immediately.",
            received_at="2026-11-19T03:34:00Z"
        ),
        InboundEmail(
            message_id="msg_inquiry_004",
            sender_name="Amira Hassan",
            sender_email="amira@digitalagency.eg",
            subject="Inquiry regarding custom Salesforce CRM connectors",
            body="Good morning! We are loving the automation suite so far. We were wondering if you have an upcoming roadmap for deep two-way Salesforce syncing?",
            received_at="2026-11-19T03:35:00Z"
        )
    ]

    results = []
    for email in scenarios:
        res = await pipeline.triage_email(email)
        results.append({
            "message_id": res.message_id,
            "sender": res.sender_email,
            "subject": res.subject,
            "detected_intent": res.intent.primary_intent,
            "detected_sentiment": res.sentiment.sentiment,
            "urgency": res.sentiment.urgency_level,
            "applied_labels": res.applied_labels,
            "knowledge_articles": res.retrieved_knowledge_articles,
            "draft_preview": res.draft_reply.body_text[:120] + "..."
        })

    return {
        "status": "success",
        "demo_count": len(results),
        "triage_summary": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("task_2_email_triage.main:app", host="0.0.0.0", port=8001, reload=True)
