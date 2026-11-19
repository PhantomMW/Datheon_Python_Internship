from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from task_1_lead_qualification.schemas import LeadInput, LeadProcessResult
from task_1_lead_qualification.pipeline import LeadQualificationPipeline

app = FastAPI(
    title="Datheon AI - Multi-Source Lead Routing & Qualification API",
    description="High-velocity lead intake, OpenAI qualification, Airtable ingestion, and Slack alert pipeline.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = LeadQualificationPipeline()


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "task_1_lead_qualification", "sla_target_seconds": 10.0}


@app.post(
    "/api/v1/leads/webhook",
    response_model=LeadProcessResult,
    status_code=status.HTTP_200_OK,
    tags=["Lead Routing"]
)
async def ingest_lead_webhook(lead: LeadInput):
    """
    Ingests lead from any webhook/form, evaluates company size & budget using AI,
    persists records to Airtable, and delivers rich talking points to Slack in <10s.
    """
    result = await pipeline.process_lead(lead)
    if result.status == "ERROR":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)
    return result


@app.post(
    "/api/v1/leads/benchmark",
    response_model=Dict[str, Any],
    tags=["Benchmarking"]
)
async def benchmark_lead_sla():
    """Simulates multi-source lead intake and measures execution latency against 10s SLA."""
    test_leads = [
        LeadInput(
            full_name="Elena Rostova",
            email="elena@megacorp.io",
            company_name="MegaCorp Global",
            company_size="500+ employees",
            estimated_budget="$75,000",
            project_scope="Autonomous agent swarm for enterprise supply chain operations",
            source="Typeform Enterprise Form"
        ),
        LeadInput(
            full_name="David Miller",
            email="david@fintechstart.co",
            company_name="Fintech Velocity",
            company_size="45 employees",
            estimated_budget="$25,000",
            project_scope="Automate payment failure outreach & Stripe webhooks",
            source="Custom Landing Page Webhook"
        ),
        LeadInput(
            full_name="Adam Wright",
            email="adam@wrightcrafts.com",
            company_name="Wright Crafts",
            company_size="4 employees",
            estimated_budget="$2,000",
            project_scope="Social media scheduler",
            source="Contact Us Widget"
        )
    ]

    results = []
    latencies = []
    for lead in test_leads:
        res = await pipeline.process_lead(lead)
        results.append({
            "company": lead.company_name,
            "tier": res.qualification.qualification_tier,
            "score": res.qualification.score,
            "latency_seconds": res.execution_time_seconds,
            "within_sla": res.within_sla
        })
        latencies.append(res.execution_time_seconds)

    avg_latency = sum(latencies) / len(latencies)
    return {
        "benchmark_summary": {
            "total_processed": len(test_leads),
            "average_latency_seconds": round(avg_latency, 3),
            "max_latency_seconds": round(max(latencies), 3),
            "sla_limit_seconds": 10.0,
            "all_within_sla": all(r["within_sla"] for r in results)
        },
        "details": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("task_1_lead_qualification.main:app", host="0.0.0.0", port=8000, reload=True)
