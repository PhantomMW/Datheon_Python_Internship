import base64
import logging
import uuid
import os
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from task_2_email_triage.config import settings

logger = logging.getLogger("GmailService")


class GmailService:
    """Manages Gmail API communication: label synchronization and automated draft creation."""

    def __init__(self, credentials_path: str = None, token_path: str = None):
        self.credentials_path = credentials_path or settings.gmail_credentials_path
        self.token_path = token_path or settings.gmail_token_path
        self.user_id = settings.gmail_triage_user_id
        self.service = self._init_service()

    def _init_service(self):
        """Initializes Google Gmail API client if credentials exist."""
        if not os.path.exists(self.credentials_path) and not os.path.exists(self.token_path):
            logger.info("Gmail credentials not detected. Operating in simulated Mock mode.")
            return None

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path)

            if creds and creds.valid:
                return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"Could not initialize Gmail API client ({str(e)}). Fallback to Mock.")

        return None

    def apply_labels(self, message_id: str, labels: List[str]) -> bool:
        """Applies triage category labels to an email thread."""
        if not self.service:
            logger.info(f"[MOCK GMAIL] Applied labels {labels} to message '{message_id}'")
            return True

        try:
            # Gmail requires labelIds. In real mode, labels would be mapped to their ID
            body = {
                "addLabelIds": labels,
                "removeLabelIds": ["UNREAD"]
            }
            self.service.users().messages().modify(userId=self.user_id, id=message_id, body=body).execute()
            logger.info(f"Successfully applied labels {labels} to message {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply Gmail labels ({str(e)})")
            return False

    def create_draft(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        thread_id: Optional[str] = None
    ) -> str:
        """Creates a polite context-aware reply as a draft in Gmail."""
        if not self.service:
            mock_draft_id = f"draft_{uuid.uuid4().hex[:12]}"
            logger.info(f"[MOCK GMAIL] Created draft '{mock_draft_id}' for recipient <{to_email}> with subject '{subject}'")
            return mock_draft_id

        try:
            message = MIMEText(body_text)
            message["to"] = to_email
            message["subject"] = subject
            if thread_id:
                message["threadId"] = thread_id

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            draft_body = {"message": {"raw": raw_message}}

            draft = self.service.users().drafts().create(userId=self.user_id, body=draft_body).execute()
            draft_id = draft.get("id", f"draft_{uuid.uuid4().hex[:12]}")
            logger.info(f"Gmail Draft created successfully: {draft_id}")
            return draft_id
        except Exception as e:
            logger.error(f"Failed to create Gmail draft ({str(e)})")
            return f"draft_fallback_{uuid.uuid4().hex[:8]}"
