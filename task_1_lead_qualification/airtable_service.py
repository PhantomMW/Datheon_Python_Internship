import logging
import uuid
from typing import Optional, Dict, Any
import httpx
from task_1_lead_qualification.schemas import LeadInput, AIQualificationResult
from task_1_lead_qualification.config import settings

logger = logging.getLogger("AirtableService")


class AirtableService:
    """Handles async record creation in Airtable with transparent mock fallback."""

    def __init__(self, api_key: str = None, base_id: str = None, table_name: str = None):
        self.api_key = api_key or settings.airtable_api_key
        self.base_id = base_id or settings.airtable_base_id
        self.table_name = table_name or settings.airtable_table_name
        self.is_configured = bool(self.api_key and self.base_id and "Mock" not in self.base_id)

    async def create_lead_record(self, lead: LeadInput, qualification: AIQualificationResult) -> str:
        """Creates a record in Airtable and returns the record ID."""
        fields: Dict[str, Any] = {
            "Full Name": lead.full_name,
            "Email": lead.email,
            "Company": lead.company_name,
            "Company Size": lead.company_size,
            "Budget": lead.estimated_budget,
            "Evaluated Budget USD": qualification.budget_evaluated_usd,
            "Qualification Tier": qualification.qualification_tier,
            "Lead Score": qualification.score,
            "Urgency": qualification.urgency,
            "Recommended Action": qualification.recommended_action,
            "Sales Talking Points": "\n".join(f"• {point}" for point in qualification.custom_sales_talking_points),
            "Lead Source": lead.source,
            "Project Scope": lead.project_scope
        }

        if not self.is_configured:
            mock_id = f"rec_{uuid.uuid4().hex[:14]}"
            logger.info(f"[MOCK AIRTABLE] Record simulated successfully for '{lead.company_name}'. Record ID: {mock_id}")
            return mock_id

        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"fields": fields}

        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            record_id = data.get("id", f"rec_{uuid.uuid4().hex[:14]}")
            logger.info(f"Airtable record created: {record_id}")
            return record_id
