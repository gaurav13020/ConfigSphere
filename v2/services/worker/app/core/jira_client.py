from __future__ import annotations

import logging
import os
from base64 import b64encode

import requests

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self) -> None:
        self.enabled = os.getenv("JIRA_ENABLED", "false").lower() == "true"
        self.base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
        self.user_email = os.getenv("JIRA_USER_EMAIL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "CS")
        self.issue_type = os.getenv("JIRA_ISSUE_TYPE", "Task")
        self.transition_map: dict[str, str] = {}
        for status_key in ("SUBMITTED", "APPROVED", "IMPLEMENTING", "IMPLEMENTED", "REJECTED"):
            tid = os.getenv(f"JIRA_TRANSITION_{status_key}", "")
            if tid:
                self.transition_map[status_key] = tid

    def _headers(self) -> dict[str, str]:
        creds = b64encode(f"{self.user_email}:{self.api_token}".encode()).decode()
        return {
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_issue(
        self,
        summary: str,
        description: str,
    ) -> tuple[str, str]:
        """Create a Jira issue. Returns (issue_key, issue_id)."""
        if not self.enabled:
            logger.info("Jira disabled, skipping issue creation: %s", summary)
            return ("", "")

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": self.issue_type},
            }
        }
        url = f"{self.base_url}/rest/api/3/issue"
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            logger.error("Jira create issue failed (%s): %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()
        issue_key = data["key"]
        issue_id = data["id"]
        logger.info("Created Jira issue %s (id=%s)", issue_key, issue_id)
        return (issue_key, issue_id)

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        """Transition a Jira issue to a new status."""
        if not self.enabled:
            logger.info("Jira disabled, skipping transition %s -> %s", issue_key, transition_id)
            return

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            logger.warning(
                "Jira transition %s -> %s returned %s (issue may have already moved past this status): %s",
                issue_key, transition_id, resp.status_code, resp.text,
            )
            return
        logger.info("Transitioned Jira issue %s via transition %s", issue_key, transition_id)

    def add_comment(self, issue_key: str, body: str) -> None:
        """Add a comment to a Jira issue."""
        if not self.enabled:
            return

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body}],
                    }
                ],
            }
        }
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        resp.raise_for_status()
