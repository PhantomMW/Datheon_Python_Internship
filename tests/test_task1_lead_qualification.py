import asyncio
import time
import pytest
from task_1_lead_qualification.schemas import LeadInput
from task_1_lead_qualification.qualifier import AILeadQualifier
from task_1_lead_qualification.airtable_service import AirtableService
from task_1_lead_qualification.slack_service import SlackService
from task_1_lead_qualification.pipeline import LeadQualificationPipeline


def test_qualifier_enterprise_tier():
    async def _run():
        qualifier = AILeadQualifier()
        lead = LeadInput(
            full_name="Samantha Ray",
            email="samantha@globalhealth.org",
            company_name="Global Health Corp",
            company_size="350 employees",
            estimated_budget="$85,000",
            project_scope="Automate patient intake data pipelines",
            source="Website Enterprise Form"
        )
        return await qualifier.qualify_lead(lead)

    result = asyncio.run(_run())
    assert result.qualification_tier == "TIER_1_ENTERPRISE"
    assert result.score >= 80
    assert result.budget_evaluated_usd == 85000.0
    assert result.urgency == "HIGH"
    assert len(result.custom_sales_talking_points) >= 2


def test_qualifier_mid_market_tier():
    async def _run():
        qualifier = AILeadQualifier()
        lead = LeadInput(
            full_name="Liam Smith",
            email="liam@cloudscale.io",
            company_name="CloudScale",
            company_size="30 employees",
            estimated_budget="$20,000",
            project_scope="Stripe & HubSpot sync",
            source="Inbound Webhook"
        )
        return await qualifier.qualify_lead(lead)

    result = asyncio.run(_run())
    assert result.qualification_tier == "TIER_2_MID_MARKET"
    assert result.score >= 60
    assert result.budget_evaluated_usd == 20000.0


def test_airtable_service_creation():
    async def _run():
        airtable = AirtableService()
        lead = LeadInput(
            full_name="Test User",
            email="test@company.com",
            company_name="Acme Corp",
            company_size="50",
            estimated_budget="$30,000"
        )
        qualifier = AILeadQualifier()
        qualification = await qualifier.qualify_lead(lead)
        return await airtable.create_lead_record(lead, qualification)

    record_id = asyncio.run(_run())
    assert record_id.startswith("rec_")


def test_slack_block_kit_formatting():
    slack = SlackService()
    lead = LeadInput(
        full_name="Test User",
        email="test@company.com",
        company_name="Acme Corp",
        company_size="50",
        estimated_budget="$30,000"
    )
    qualifier = AILeadQualifier()
    qualification = qualifier._heuristic_qualification(lead)

    payload = slack.format_slack_message(lead, qualification, "rec_12345", 1.25)
    assert "blocks" in payload
    assert len(payload["blocks"]) >= 4
    found_talking_points = any("Talking Points" in str(b) for b in payload["blocks"])
    assert found_talking_points is True


def test_end_to_end_pipeline_under_10_seconds_sla():
    """Validates the core deliverable: execution end-to-end in under 10 seconds."""
    async def _run():
        pipeline = LeadQualificationPipeline()
        lead = LeadInput(
            full_name="Dr. Evelyn Reed",
            email="evelyn@reedhealth.org",
            company_name="Reed Health Systems",
            company_size="120 employees",
            estimated_budget="$55,000",
            project_scope="Medical records triage automation",
            source="Enterprise Lead Ingestion"
        )
        start = time.perf_counter()
        res = await pipeline.process_lead(lead)
        duration = time.perf_counter() - start
        return res, duration

    result, duration = asyncio.run(_run())

    assert result.status == "SUCCESS"
    assert result.within_sla is True
    assert duration < 10.0
    assert result.execution_time_seconds < 10.0
    assert result.airtable_record_id is not None
    assert result.slack_alert_sent is True
    assert result.qualification.score > 0
