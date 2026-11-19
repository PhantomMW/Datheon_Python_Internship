import asyncio
import pytest
from task_2_email_triage.schemas import InboundEmail
from task_2_email_triage.knowledge_base.retriever import KnowledgeRetriever
from task_2_email_triage.triage_agent import EmailTriageAgent
from task_2_email_triage.pipeline import EmailTriagePipeline


def test_knowledge_base_retriever_billing():
    retriever = KnowledgeRetriever()
    results = retriever.search("I need a refund for duplicate invoice charge", top_k=2)
    assert len(results) > 0
    categories = [r.category for r in results]
    assert "BILLING" in categories


def test_knowledge_base_retriever_outage():
    retriever = KnowledgeRetriever()
    results = retriever.search("API 500 error server down outage incident", top_k=2)
    assert len(results) > 0
    ids = [r.id for r in results]
    assert "KB-201" in ids


def test_urgent_outage_triage():
    async def _run():
        pipeline = EmailTriagePipeline()
        email = InboundEmail(
            message_id="msg_test_001",
            sender_name="Daniel Wright",
            sender_email="daniel@wrightlogistics.net",
            subject="CRITICAL: Entire API is down with 500 errors",
            body="All our webhook pipelines are failing and production is halted. Urgent assistance needed ASAP!"
        )
        return await pipeline.triage_email(email)

    result = asyncio.run(_run())
    assert result.intent.primary_intent == "URGENT_OUTAGE"
    assert result.sentiment.urgency_level == "HIGH"
    assert "Priority/Urgent" in result.applied_labels
    assert "Intent/URGENT_OUTAGE" in result.applied_labels
    assert result.draft_reply.draft_id is not None
    assert "Re: CRITICAL" in result.draft_reply.subject
    assert "apologize" in result.draft_reply.body_text.lower() or "investigating" in result.draft_reply.body_text.lower()


def test_billing_and_frustrated_sentiment_triage():
    async def _run():
        pipeline = EmailTriagePipeline()
        email = InboundEmail(
            message_id="msg_test_002",
            sender_name="Karen Green",
            sender_email="kgreen@retail.com",
            subject="Unacceptable duplicate invoice charges",
            body="I am furious about this billing mistake. You charged my credit card twice. Refund this immediately or I will cancel!"
        )
        return await pipeline.triage_email(email)

    result = asyncio.run(_run())
    assert result.intent.primary_intent in ["BILLING_QUERY", "CANCELLATION_REQUEST"]
    assert result.sentiment.sentiment in ["FRUSTRATED", "ANGRY"]
    assert result.sentiment.polarity_score < 0
    assert "Status/Draft-Created" in result.applied_labels
    assert "refund" in result.draft_reply.body_text.lower() or "billing" in result.draft_reply.body_text.lower()
