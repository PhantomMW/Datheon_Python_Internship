import time
import logging
from typing import Optional, List
from task_2_email_triage.schemas import InboundEmail, EmailTriageResult
from task_2_email_triage.triage_agent import EmailTriageAgent
from task_2_email_triage.gmail_service import GmailService
from task_2_email_triage.config import settings

logger = logging.getLogger("EmailTriagePipeline")


class EmailTriagePipeline:
    """Coordinates autonomous inbox triage, sentiment/intent evaluation, tagging, and draft creation."""

    def __init__(
        self,
        agent: Optional[EmailTriageAgent] = None,
        gmail: Optional[GmailService] = None
    ):
        self.agent = agent or EmailTriageAgent()
        self.gmail = gmail or GmailService()

    async def triage_email(self, email: InboundEmail) -> EmailTriageResult:
        """Processes an inbound email from Gmail/Outlook end-to-end."""
        start_time = time.perf_counter()
        logger.info(f"Initiating triage for email '{email.subject}' from <{email.sender_email}>")

        # 1. AI Analysis & Draft Synthesis
        sentiment, intent, draft, kb_titles = await self.agent.analyze_and_draft(email)

        # 2. Formulate dynamic labels
        labels: List[str] = [f"Intent/{intent.primary_intent}"]

        if sentiment.urgency_level == "HIGH" or sentiment.escalation_needed:
            labels.append("Priority/Urgent")
        else:
            labels.append("Priority/Normal")

        if sentiment.sentiment in ["FRUSTRATED", "ANGRY"]:
            labels.append(f"Sentiment/{sentiment.sentiment}")

        # 3. Apply labels to Gmail thread/message
        self.gmail.apply_labels(message_id=email.message_id, labels=labels)

        # 4. Create context-aware draft in Gmail
        if settings.autonomous_draft_enabled:
            draft_id = self.gmail.create_draft(
                to_email=draft.recipient,
                subject=draft.subject,
                body_text=draft.body_text,
                thread_id=email.thread_id
            )
            draft.draft_id = draft_id
            labels.append("Status/Draft-Created")

        elapsed = time.perf_counter() - start_time
        logger.info(f"Triage completed for '{email.message_id}' in {elapsed:.3f}s. Intent: {intent.primary_intent}")

        return EmailTriageResult(
            message_id=email.message_id,
            sender_email=email.sender_email,
            subject=email.subject,
            sentiment=sentiment,
            intent=intent,
            applied_labels=labels,
            retrieved_knowledge_articles=kb_titles,
            draft_reply=draft,
            processing_time_seconds=round(elapsed, 4),
            status="PROCESSED"
        )
