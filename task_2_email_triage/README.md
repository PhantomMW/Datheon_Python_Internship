# Task 2: Autonomous Customer Support & Intelligent Email Triage

> **Difficulty**: Intermediate  
> **Stack**: Make.com, Gmail API / Outlook, OpenAI, Python 3.10+ (FastAPI)  
> **Key Deliverable**: Autonomous inbox triage system with automatic tagging and draft generation.

---

## 🎯 Objective
Connect Gmail / Outlook to an AI agent that monitors incoming emails, performs sentiment analysis (positive, neutral, frustrated, angry), identifies urgent tickets vs billing queries vs technical support, searches an internal knowledge base, tags/labels threads in Gmail, and crafts polite, human-like draft responses ready for one-click review or autonomous sending.

---

## 🏗️ Architecture & Workflow

```text
  [ Inbound Gmail / Outlook Email ]
                 │
                 ▼
     [ OpenAI Triage Agent ]
       • Sentiment Polarity Detection (-1.0 to 1.0)
       • Intent Categorization (Outage, Billing, Tech, Refund)
       • Urgency Assessment (High / Medium / Low)
                 │
                 ▼
    [ Internal Knowledge Base Search ]
       • Matches relevant FAQ, SLA, and Billing policies
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[ Gmail Labeling ]    [ Gmail Draft Creation ]
• Intent/URGENT_OUTAGE  • Drafts Polite Context-Aware Response
• Priority/Urgent      • Quotes relevant policies & SLAs
• Sentiment/Frustrated • Prepares Draft in existing thread
```

---

## 📦 Make.com Blueprint Import Guide

The full scenario blueprint is available at [`blueprints/make_email_triage_blueprint.json`](blueprints/make_email_triage_blueprint.json).

### Steps to Import:
1. Open **Make.com** and navigate to **Scenarios** -> **Create a new scenario**.
2. Click the three dots (`...`) in the bottom bar and select **Import Blueprint**.
3. Choose `task_2_email_triage/blueprints/make_email_triage_blueprint.json`.
4. Connect the modules:
   - **Gmail (Watch Emails)**: Authorize your Gmail / Google Workspace account.
   - **OpenAI**: Connect your API key and configure model `gpt-4o-mini`.
   - **Gmail (Add Labels)**: Select the target inbox label taxonomy.
   - **Gmail (Create a Draft)**: Ensure thread mapping is linked.
5. Save and schedule scenario to run every 5 or 15 minutes.

---

## 💻 Python Service & Execution

### Run the FastAPI Service:
```bash
uvicorn task_2_email_triage.main:app --host 0.0.0.0 --port 8001 --reload
```

### Ingest an Email via cURL / HTTP:
```bash
curl -X POST http://localhost:8001/api/v1/triage/process \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_90182_prod",
    "sender_email": "cto@fintechclient.com",
    "sender_name": "Sarah Jenkins",
    "subject": "URGENT: Webhook delivery 500 error down in production",
    "body": "Hello, our production webhook receivers are timing out with 500 errors. We have transactions stalled. Please investigate immediately!"
  }'
```

### Sample Output:
```json
{
  "message_id": "msg_90182_prod",
  "sender_email": "cto@fintechclient.com",
  "subject": "URGENT: Webhook delivery 500 error down in production",
  "sentiment": {
    "sentiment": "FRUSTRATED",
    "polarity_score": -0.7,
    "urgency_level": "HIGH",
    "escalation_needed": true
  },
  "intent": {
    "primary_intent": "URGENT_OUTAGE",
    "confidence": 0.92,
    "secondary_intents": []
  },
  "applied_labels": [
    "Intent/URGENT_OUTAGE",
    "Priority/Urgent",
    "Sentiment/FRUSTRATED",
    "Status/Draft-Created"
  ],
  "retrieved_knowledge_articles": [
    "Urgent Production Outage & Service Disruption Protocols"
  ],
  "draft_reply": {
    "draft_id": "draft_a8b9c1d2e3f4",
    "subject": "Re: URGENT: Webhook delivery 500 error down in production",
    "body_text": "Hi Sarah Jenkins,\n\nThank you for contacting our support team. We sincerely apologize for the disruption...",
    "recipient": "cto@fintechclient.com"
  },
  "processing_time_seconds": 0.082,
  "status": "PROCESSED"
}
```

---

## 🧪 Interactive Support Demo
Execute the built-in multi-scenario test suite:
```bash
curl -X GET http://localhost:8001/api/v1/triage/demo
```
This processes 4 real-world test cases (Production Outage, Double Charge Billing Query, Angry Refund Request, and Integration Roadmap Question) and displays the triage classification and generated drafts for each.
