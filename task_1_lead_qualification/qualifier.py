import re
import json
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from task_1_lead_qualification.schemas import LeadInput, AIQualificationResult
from task_1_lead_qualification.config import settings

logger = logging.getLogger("LeadQualifier")


class AILeadQualifier:
    """Evaluates inbound leads using OpenAI with structured qualification logic."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def qualify_lead(self, lead: LeadInput) -> AIQualificationResult:
        """Evaluates company size and budget to generate lead tier and custom talking points."""
        if self.client:
            try:
                return await self._qualify_with_openai(lead)
            except Exception as e:
                logger.warning(f"OpenAI API call failed or timed out ({str(e)}). Falling back to heuristic qualification engine.")

        return self._heuristic_qualification(lead)

    async def _qualify_with_openai(self, lead: LeadInput) -> AIQualificationResult:
        system_prompt = (
            "You are an expert enterprise B2B sales development AI for an automation agency. "
            "Analyze the inbound lead and respond with a strict JSON object evaluating budget, "
            "company size, qualification tier (TIER_1_ENTERPRISE, TIER_2_MID_MARKET, TIER_3_SMB, UNQUALIFIED), "
            "lead score (0-100), urgency (HIGH, MEDIUM, LOW), and 3-4 highly tailored custom talking points for sales reps."
        )

        user_content = json.dumps({
            "full_name": lead.full_name,
            "email": lead.email,
            "company_name": lead.company_name,
            "company_size": lead.company_size,
            "estimated_budget": lead.estimated_budget,
            "project_scope": lead.project_scope,
            "source": lead.source
        })

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Qualify this lead and output in JSON format with fields: qualification_tier, score, budget_evaluated_usd, company_size_headcount, reasoning, urgency, custom_sales_talking_points (list of strings), recommended_action.\nLead data:\n{user_content}"
                }
            ],
            timeout=7.0  # Guarantees staying well under the 10-second SLA
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)

        return AIQualificationResult(
            qualification_tier=data.get("qualification_tier", "TIER_2_MID_MARKET"),
            score=int(data.get("score", 75)),
            budget_evaluated_usd=float(data.get("budget_evaluated_usd", 25000.0)),
            company_size_headcount=int(data.get("company_size_headcount", 50)),
            reasoning=data.get("reasoning", "Evaluated based on provided company size and budget parameters."),
            urgency=data.get("urgency", "MEDIUM"),
            custom_sales_talking_points=data.get("custom_sales_talking_points", [
                f"Reference potential ROI for {lead.company_name}",
                "Inquire about timeline and team buy-in",
                "Highlight automated workflow scalability"
            ]),
            recommended_action=data.get("recommended_action", "Schedule discovery call")
        )

    def _heuristic_qualification(self, lead: LeadInput) -> AIQualificationResult:
        """Deterministic offline fallback ensuring 100% uptime and sub-second evaluation."""
        # Extract numeric budget
        budget_str = re.sub(r"[^\d.]", "", lead.estimated_budget)
        budget = float(budget_str) if budget_str else 15000.0

        # Extract numeric size
        size_digits = re.findall(r"\d+", lead.company_size)
        size = int(size_digits[0]) if size_digits else 25

        # Qualification tier logic
        if budget >= 40000 or size >= 100:
            tier = "TIER_1_ENTERPRISE"
            score = min(98, 85 + int(budget / 10000))
            urgency = "HIGH"
            action = "Assign to Senior Enterprise Account Executive within 15 minutes"
            talking_points = [
                f"Emphasize enterprise governance, SOC-2 readiness, and dedicated support for {lead.company_name}",
                f"Align custom automation roadmap with high-headcount workflow optimization ({size}+ seats)",
                f"Present case studies of teams achieving 5x ROI on budgets around ${budget:,.0f}"
            ]
        elif budget >= 15000 or size >= 20:
            tier = "TIER_2_MID_MARKET"
            score = 75
            urgency = "MEDIUM"
            action = "Trigger automated calendar invite and assign Mid-Market Rep"
            talking_points = [
                f"Position rapid-deployment starter pack within the ${budget:,.0f} budget envelope",
                f"Discuss automation bottlenecks across their {size}-person organization",
                "Offer a 14-day proof of concept targeting lead routing and CRM synchronization"
            ]
        elif budget >= 5000:
            tier = "TIER_3_SMB"
            score = 55
            urgency = "LOW"
            action = "Send self-serve onboarding guide and modular pricing sheet"
            talking_points = [
                "Recommend self-service modular automation templates",
                "Review immediate high-impact quick wins before scaling to custom development"
            ]
        else:
            tier = "UNQUALIFIED"
            score = 30
            urgency = "LOW"
            action = "Direct to community documentation and asynchronous resources"
            talking_points = [
                "Budget below minimum threshold for custom enterprise engineering",
                "Provide link to free automation starter kits"
            ]

        return AIQualificationResult(
            qualification_tier=tier,
            score=score,
            budget_evaluated_usd=budget,
            company_size_headcount=size,
            reasoning=f"Analyzed lead profile for {lead.company_name}: Reported size of ~{size} employees and estimated budget of ${budget:,.0f}.",
            urgency=urgency,
            custom_sales_talking_points=talking_points,
            recommended_action=action
        )
