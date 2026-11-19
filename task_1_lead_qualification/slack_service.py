import logging
from typing import Dict, Any, List
import httpx
from task_1_lead_qualification.schemas import LeadInput, AIQualificationResult
from task_1_lead_qualification.config import settings

logger = logging.getLogger("SlackService")


class SlackService:
    """Dispatches rich Block Kit notifications to Slack sales channels."""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or settings.slack_webhook_url
        self.is_configured = bool(self.webhook_url and "hooks.slack.com" in self.webhook_url)

    def format_slack_message(
        self,
        lead: LeadInput,
        qualification: AIQualificationResult,
        airtable_id: str,
        duration_s: float
    ) -> Dict[str, Any]:
        """Constructs a Slack Block Kit payload with customized talking points."""
        tier_emojis = {
            "TIER_1_ENTERPRISE": "🔥 🚀",
            "TIER_2_MID_MARKET": "⭐",
            "TIER_3_SMB": "🌱",
            "UNQUALIFIED": "⚪"
        }
        emoji = tier_emojis.get(qualification.qualification_tier, "💼")

        talking_points_text = "\n".join(f"• {point}" for point in qualification.custom_sales_talking_points)

        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} New Lead Qualified: {lead.company_name} ({qualification.qualification_tier})",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Contact:*\n{lead.full_name} (<mailto:{lead.email}|{lead.email}>)"},
                    {"type": "mrkdwn", "text": f"*Company Size:*\n{lead.company_size}"},
                    {"type": "mrkdwn", "text": f"*Stated Budget:*\n{lead.estimated_budget} (${qualification.budget_evaluated_usd:,.0f})"},
                    {"type": "mrkdwn", "text": f"*Score & Urgency:*\n`{qualification.score}/100` | *{qualification.urgency}*"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 Custom Sales Talking Points:*\n{talking_points_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚡ Recommended Next Step:*\n_{qualification.recommended_action}_"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🏷️ *Airtable Record:* `{airtable_id}` | ⏱️ *Processed in:* `{duration_s:.2f}s` (SLA: <10s) | 🌐 *Source:* {lead.source}"
                    }
                ]
            }
        ]

        return {
            "channel": settings.slack_sales_channel,
            "blocks": blocks,
            "text": f"New Lead Alert: {lead.company_name} - Score {qualification.score}/100"
        }

    async def send_sales_alert(
        self,
        lead: LeadInput,
        qualification: AIQualificationResult,
        airtable_id: str,
        duration_s: float
    ) -> bool:
        """Sends the notification payload via Slack Incoming Webhook."""
        payload = self.format_slack_message(lead, qualification, airtable_id, duration_s)

        if not self.is_configured:
            logger.info(f"[MOCK SLACK ALERT] Successfully dispatched alert for '{lead.company_name}' in {duration_s:.2f}s")
            return True

        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Slack alert posted successfully.")
            return True
