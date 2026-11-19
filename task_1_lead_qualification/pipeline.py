import time
import asyncio
import logging
import uuid
from typing import Optional
from task_1_lead_qualification.schemas import LeadInput, LeadProcessResult, AIQualificationResult
from task_1_lead_qualification.qualifier import AILeadQualifier
from task_1_lead_qualification.airtable_service import AirtableService
from task_1_lead_qualification.slack_service import SlackService
from task_1_lead_qualification.config import settings

logger = logging.getLogger("LeadPipeline")


class LeadQualificationPipeline:
    """Orchestrates end-to-end ingestion, AI evaluation, Airtable persistence, and Slack alerting."""

    def __init__(
        self,
        qualifier: Optional[AILeadQualifier] = None,
        airtable: Optional[AirtableService] = None,
        slack: Optional[SlackService] = None
    ):
        self.qualifier = qualifier or AILeadQualifier()
        self.airtable = airtable or AirtableService()
        self.slack = slack or SlackService()

    async def process_lead(self, lead: LeadInput) -> LeadProcessResult:
        """Processes lead end-to-end and strictly monitors sub-10 second execution SLA."""
        start_time = time.perf_counter()
        lead_id = f"lead_{uuid.uuid4().hex[:10]}"
        logger.info(f"Starting lead processing for '{lead.company_name}' (ID: {lead_id})")

        try:
            # 1. Step: AI Evaluation
            qualification: AIQualificationResult = await self.qualifier.qualify_lead(lead)

            # 2. Step: Airtable Persistence & Slack Notification concurrently
            # First create Airtable record or resolve record ID
            airtable_task = self.airtable.create_lead_record(lead, qualification)
            airtable_id = await airtable_task

            # Intermediate timing for Slack context
            interim_duration = time.perf_counter() - start_time

            # 3. Step: Send Slack alert
            slack_alert_task = self.slack.send_sales_alert(
                lead=lead,
                qualification=qualification,
                airtable_id=airtable_id,
                duration_s=interim_duration
            )
            slack_success = await slack_alert_task

            # 4. Total duration and SLA check
            total_duration = time.perf_counter() - start_time
            within_sla = total_duration <= settings.max_execution_sla_seconds

            logger.info(
                f"Completed lead processing for '{lead.company_name}' in {total_duration:.3f}s. "
                f"SLA Met: {within_sla} (Limit: {settings.max_execution_sla_seconds}s)"
            )

            return LeadProcessResult(
                lead_id=lead_id,
                status="SUCCESS",
                within_sla=within_sla,
                execution_time_seconds=round(total_duration, 4),
                qualification=qualification,
                airtable_record_id=airtable_id,
                slack_alert_sent=slack_success,
                message=f"Lead qualified in {total_duration:.2f}s (Tier: {qualification.qualification_tier}, Score: {qualification.score})"
            )

        except Exception as e:
            total_duration = time.perf_counter() - start_time
            logger.error(f"Error processing lead '{lead.company_name}': {str(e)}", exc_info=True)
            return LeadProcessResult(
                lead_id=lead_id,
                status="ERROR",
                within_sla=total_duration <= settings.max_execution_sla_seconds,
                execution_time_seconds=round(total_duration, 4),
                qualification=AIQualificationResult(
                    qualification_tier="UNQUALIFIED",
                    score=0,
                    budget_evaluated_usd=0.0,
                    company_size_headcount=0,
                    reasoning=f"Pipeline failure: {str(e)}",
                    urgency="LOW",
                    custom_sales_talking_points=["Follow up manually due to automated intake error"],
                    recommended_action="Manual review required"
                ),
                airtable_record_id=None,
                slack_alert_sent=False,
                message=f"Failed to qualify lead: {str(e)}"
            )
