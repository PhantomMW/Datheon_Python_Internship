import json
import logging
from typing import Dict, Any, Tuple
from openai import AsyncOpenAI
from task_2_email_triage.schemas import (
    InboundEmail,
    SentimentAnalysis,
    IntentClassification,
    DraftReply
)
from task_2_email_triage.knowledge_base.retriever import KnowledgeRetriever
from task_2_email_triage.config import settings

logger = logging.getLogger("EmailTriageAgent")


class EmailTriageAgent:
    """Autonomous agent for customer support intent classification, sentiment analysis, and draft synthesis."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.retriever = KnowledgeRetriever()

    async def analyze_and_draft(self, email: InboundEmail) -> Tuple[SentimentAnalysis, IntentClassification, DraftReply, list]:
        """Runs end-to-end triage: sentiment, intent, KB lookup, and polite draft generation."""
        # 1. Retrieve knowledge base articles relevant to the email
        search_query = f"{email.subject} {email.body}"
        kb_articles = self.retriever.search(search_query, top_k=2)
        kb_context = self.retriever.get_context_summary(search_query)

        if self.client:
            try:
                return await self._analyze_with_openai(email, kb_context, kb_articles)
            except Exception as e:
                logger.warning(f"OpenAI call failed ({str(e)}). Running heuristic agent fallback.")

        return self._heuristic_analysis(email, kb_articles)

    async def _analyze_with_openai(
        self,
        email: InboundEmail,
        kb_context: str,
        kb_articles: list
    ) -> Tuple[SentimentAnalysis, IntentClassification, DraftReply, list]:
        system_prompt = (
            "You are an autonomous senior customer support specialist. "
            "Analyze the inbound customer email and output strict JSON with:\n"
            "1. sentiment: (POSITIVE, NEUTRAL, FRUSTRATED, ANGRY)\n"
            "2. polarity_score: (float -1.0 to 1.0)\n"
            "3. urgency_level: (HIGH, MEDIUM, LOW)\n"
            "4. escalation_needed: (boolean)\n"
            "5. primary_intent: (URGENT_OUTAGE, BILLING_QUERY, TECHNICAL_SUPPORT, CANCELLATION_REQUEST, FEATURE_REQUEST, GENERAL_INQUIRY)\n"
            "6. confidence: (float 0.0 to 1.0)\n"
            "7. draft_subject: (reply subject string like 'Re: ...')\n"
            "8. draft_body_text: (polite, warm, context-aware reply using the provided Knowledge Base facts)\n"
            "9. draft_body_html: (HTML formatted reply)"
        )

        user_content = json.dumps({
            "sender_name": email.sender_name,
            "sender_email": email.sender_email,
            "subject": email.subject,
            "body": email.body,
            "knowledge_base_reference": kb_context
        })

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Triage email and generate polite response:\n{user_content}"}
            ],
            timeout=8.0
        )

        data = json.loads(response.choices[0].message.content)

        sentiment = SentimentAnalysis(
            sentiment=data.get("sentiment", "NEUTRAL"),
            polarity_score=float(data.get("polarity_score", 0.0)),
            urgency_level=data.get("urgency_level", "MEDIUM"),
            escalation_needed=bool(data.get("escalation_needed", False))
        )

        intent = IntentClassification(
            primary_intent=data.get("primary_intent", "GENERAL_INQUIRY"),
            confidence=float(data.get("confidence", 0.85)),
            secondary_intents=[]
        )

        body_text = data.get("draft_body_text", "")
        body_html = data.get("draft_body_html", f"<p>{body_text.replace(chr(10), '<br>')}</p>")
        reply_subject = data.get("draft_subject", f"Re: {email.subject}")

        draft = DraftReply(
            subject=reply_subject,
            body_text=body_text,
            body_html=body_html,
            recipient=email.sender_email
        )

        return sentiment, intent, draft, [doc.title for doc in kb_articles]

    def _heuristic_analysis(
        self,
        email: InboundEmail,
        kb_articles: list
    ) -> Tuple[SentimentAnalysis, IntentClassification, DraftReply, list]:
        """Reliable heuristic fallback ensuring sub-second triage without external API dependency."""
        full_text = f"{email.subject} {email.body}".lower()

        # Sentiment detection
        frustrated_triggers = ["broken", "furious", "unacceptable", "terrible", "immediately", "angry", "waste", "disaster"]
        urgent_triggers = ["urgent", "down", "outage", "production", "critical", "emergency", "asap", "500 error"]
        billing_triggers = ["bill", "invoice", "charge", "refund", "receipt", "cancel", "subscription", "credit card"]

        is_urgent = any(w in full_text for w in urgent_triggers)
        is_frustrated = any(w in full_text for w in frustrated_triggers)
        is_billing = any(w in full_text for w in billing_triggers)

        if is_frustrated:
            sentiment_label = "FRUSTRATED" if not ("furious" in full_text or "terrible" in full_text) else "ANGRY"
            polarity = -0.7
            escalation = True
        elif "thank" in full_text or "great" in full_text:
            sentiment_label = "POSITIVE"
            polarity = 0.8
            escalation = False
        else:
            sentiment_label = "NEUTRAL"
            polarity = 0.0
            escalation = False

        # Intent classification
        if is_urgent:
            primary_intent = "URGENT_OUTAGE"
            urgency = "HIGH"
            escalation = True
        elif is_billing:
            if "refund" in full_text or "cancel" in full_text:
                primary_intent = "CANCELLATION_REQUEST"
                urgency = "HIGH" if is_frustrated else "MEDIUM"
            else:
                primary_intent = "BILLING_QUERY"
                urgency = "MEDIUM"
        elif "api" in full_text or "error" in full_text or "bug" in full_text:
            primary_intent = "TECHNICAL_SUPPORT"
            urgency = "MEDIUM"
        else:
            primary_intent = "GENERAL_INQUIRY"
            urgency = "LOW"

        sentiment = SentimentAnalysis(
            sentiment=sentiment_label,
            polarity_score=polarity,
            urgency_level=urgency,
            escalation_needed=escalation
        )

        intent = IntentClassification(
            primary_intent=primary_intent,
            confidence=0.92,
            secondary_intents=[]
        )

        # Knowledge base extraction & draft synthesis
        article_titles = [doc.title for doc in kb_articles] if kb_articles else ["Support Knowledge Base"]
        first_doc = kb_articles[0] if kb_articles else None

        recipient_name = email.sender_name or "Valued Customer"

        if primary_intent == "URGENT_OUTAGE":
            body_text = (
                f"Hi {recipient_name},\n\n"
                "Thank you for contacting our support team. We sincerely apologize for the disruption you experienced.\n\n"
                "Our Site Reliability Engineering (SRE) team is already actively investigating the reported service incident. "
                "You can track real-time remediation updates on our public status page at https://status.datheon.ai.\n\n"
                "Per our Enterprise SLA, your account is protected with automatic downtime credits, and we will follow up with "
                "a comprehensive post-incident summary once all services are operating nominally.\n\n"
                "Warm regards,\nDatheon Support Automation"
            )
        elif primary_intent in ["BILLING_QUERY", "CANCELLATION_REQUEST"]:
            body_text = (
                f"Hi {recipient_name},\n\n"
                "Thank you for reaching out regarding your account billing.\n\n"
                "We understand how important this is and want to assure you that our billing team has flagged your request. "
                "Per our policy, all refund and invoice adjustments are processed within 24 to 48 business hours with zero penalty.\n\n"
                "If you need an updated invoice or transaction receipt, we will email it directly to you once generated.\n\n"
                "Best regards,\nDatheon Billing Operations"
            )
        else:
            doc_context = first_doc.content if first_doc else "Our team is here to assist with your configuration."
            body_text = (
                f"Hi {recipient_name},\n\n"
                "Thank you for reaching out to Datheon support.\n\n"
                f"Regarding your inquiry, here is the relevant guidance from our documentation:\n\n"
                f"\"{doc_context}\"\n\n"
                "Please let us know if you need any additional clarification or have follow-up questions!\n\n"
                "Best regards,\nDatheon Customer Support"
            )

        body_html = f"<div style='font-family: sans-serif; line-height: 1.5;'><p>{body_text.replace(chr(10), '<br>')}</p></div>"

        draft = DraftReply(
            subject=f"Re: {email.subject}" if not email.subject.startswith("Re:") else email.subject,
            body_text=body_text,
            body_html=body_html,
            recipient=email.sender_email
        )

        return sentiment, intent, draft, article_titles
