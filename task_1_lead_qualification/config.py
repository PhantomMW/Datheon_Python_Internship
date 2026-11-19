import os
from pydantic import BaseModel, Field

# Load optional .env file if it exists
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass


class Task1Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    airtable_api_key: str = Field(default_factory=lambda: os.getenv("AIRTABLE_API_KEY", ""))
    airtable_base_id: str = Field(default_factory=lambda: os.getenv("AIRTABLE_BASE_ID", "appMockBaseId"))
    airtable_table_name: str = Field(default_factory=lambda: os.getenv("AIRTABLE_TABLE_NAME", "Leads"))

    slack_webhook_url: str = Field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL", ""))
    slack_sales_channel: str = Field(default_factory=lambda: os.getenv("SLACK_SALES_CHANNEL", "#sales-leads"))

    max_execution_sla_seconds: float = Field(default_factory=lambda: float(os.getenv("MAX_EXECUTION_SLA_SECONDS", "10.0")))
    mock_external_services_fallback: bool = Field(default_factory=lambda: os.getenv("MOCK_EXTERNAL_SERVICES_FALLBACK", "true").lower() == "true")


settings = Task1Settings()
