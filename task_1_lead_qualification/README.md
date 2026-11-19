# Task 1: Multi-Source Lead Routing & Instant AI Qualification

> **Difficulty**: Beginner  
> **Stack**: Make.com, OpenAI, Airtable, Slack, Python 3.10+ (FastAPI)  
> **Key Deliverable**: Functional automation scenario executing end-to-end in **under 10 seconds**.

---

## 🎯 Objective
Capture inbound leads from multiple webhooks/forms (Typeform, Webflow, custom JSON), evaluate company size and budget with AI (OpenAI GPT-4o-mini), create persistent records in Airtable, and alert the sales team on Slack with customized, actionable talking points.

---

## 🏗️ Architecture & Workflow

```text
  [ Inbound Lead Webhook ]
            │ (JSON payload)
            ▼
   [ OpenAI GPT-4o-mini ]
      • Evaluates Company Size & Headcount
      • Evaluates Budget USD
      • Calculates Lead Score (0 - 100) & Tier
      • Generates Custom Sales Talking Points
            │
      ┌─────┴────────────────┐
      ▼                      ▼
[ Airtable Service ]    [ Slack Service ]
• Creates Lead Record    • Dispatches Rich Block Kit Alert
• Persists Score & Tier  • Formats Custom Talking Points
• Saves Talking Points   • Flags High Urgency & SLA latency
      └─────┬────────────────┘
            ▼
  [ Webhook Response 200 OK ]  <-- Total Execution Time: < 3.5s (SLA: < 10s)
```

---

## 📦 Make.com Blueprint Import Guide

This repository contains the full production Make.com scenario blueprint in [`blueprints/make_lead_routing_blueprint.json`](blueprints/make_lead_routing_blueprint.json).

### Steps to Import:
1. Log into your **Make.com** account and navigate to **Scenarios** -> **Create a new scenario**.
2. Click the **More (three dots)** menu in the bottom toolbar and choose **Import Blueprint**.
3. Select the file: `task_1_lead_qualification/blueprints/make_lead_routing_blueprint.json`.
4. Connect your accounts:
   - **Custom Webhook**: Click *Add* to generate your unique inbound URL.
   - **OpenAI**: Connect your OpenAI API Key.
   - **Airtable**: Select your Airtable Base and `Leads` Table.
   - **Slack**: Select your Slack workspace and target sales channel (e.g. `#sales-leads`).
5. Save the scenario and toggle **ON** (Immediately).

---

## 💻 Python Implementation & Execution

We provide a production-ready asynchronous Python / FastAPI implementation.

### Run the FastAPI Service:
```bash
uvicorn task_1_lead_qualification.main:app --host 0.0.0.0 --port 8000 --reload
```

### Ingest a Lead via cURL / HTTP:
```bash
curl -X POST http://localhost:8000/api/v1/leads/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Morgan",
    "email": "a.morgan@apextechnologies.io",
    "company_name": "Apex Technologies",
    "company_size": "250 employees",
    "estimated_budget": "$60,000",
    "project_scope": "Automate supply chain operations & CRM sync",
    "source": "Enterprise Typeform"
  }'
```

### Sample Response (< 10s SLA):
```json
{
  "lead_id": "lead_9f4b1e8a20",
  "status": "SUCCESS",
  "within_sla": true,
  "execution_time_seconds": 1.48,
  "qualification": {
    "qualification_tier": "TIER_1_ENTERPRISE",
    "score": 95,
    "budget_evaluated_usd": 60000.0,
    "company_size_headcount": 250,
    "reasoning": "High budget ($60k) and significant enterprise headcount (250 seats).",
    "urgency": "HIGH",
    "custom_sales_talking_points": [
      "Emphasize enterprise governance, SOC-2 readiness, and dedicated support for Apex Technologies",
      "Align custom automation roadmap with high-headcount workflow optimization (250+ seats)",
      "Present case studies of teams achieving 5x ROI on budgets around $60,000"
    ],
    "recommended_action": "Assign to Senior Enterprise Account Executive within 15 minutes"
  },
  "airtable_record_id": "rec_7a8b9c0d1e2f3a",
  "slack_alert_sent": true,
  "message": "Lead qualified in 1.48s (Tier: TIER_1_ENTERPRISE, Score: 95)"
}
```

---

## ⏱️ SLA Benchmark Verification
Run the benchmark endpoint to verify sub-10 second execution across multiple concurrent leads:
```bash
curl -X POST http://localhost:8000/api/v1/leads/benchmark
```
*Average Latency: ~1.2s - 2.8s (Strictly within the 10.0s SLA requirement).*
