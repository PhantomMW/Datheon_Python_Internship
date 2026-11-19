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


class Task2Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    gmail_credentials_path: str = Field(default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
    gmail_token_path: str = Field(default_factory=lambda: os.getenv("GMAIL_TOKEN_PATH", "token.json"))
    gmail_triage_user_id: str = Field(default_factory=lambda: os.getenv("GMAIL_TRIAGE_USER_ID", "me"))

    urgent_sentiment_threshold: float = Field(default_factory=lambda: float(os.getenv("URGENT_SENTIMENT_THRESHOLD", "0.35")))
    autonomous_draft_enabled: bool = Field(default_factory=lambda: os.getenv("AUTONOMOUS_DRAFT_ENABLED", "true").lower() == "true")
    mock_external_services_fallback: bool = Field(default_factory=lambda: os.getenv("MOCK_EXTERNAL_SERVICES_FALLBACK", "true").lower() == "true")


settings = Task2Settings()
