"""Notification channel implementations."""

import hashlib
import hmac
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Base class for notification channels."""

    channel_type: str

    @abstractmethod
    async def send(self, leads: list[dict[str, Any]], config: dict[str, Any]) -> bool:
        """Send leads to this channel. Returns True on success."""
        ...


class SlackChannel(NotificationChannel):
    """Send leads to a Slack webhook using Block Kit formatting."""

    channel_type = "slack"

    async def send(self, leads: list[dict[str, Any]], config: dict[str, Any]) -> bool:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Slack channel missing webhook_url")
            return False

        blocks = self._build_blocks(leads)
        payload = {"blocks": blocks}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error("Slack webhook failed: %s %s", response.status_code, response.text)
                return False

        logger.info("Sent %d leads to Slack", len(leads))
        return True

    def _build_blocks(self, leads: list[dict[str, Any]]) -> list[dict]:
        blocks: list[dict] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Landscraper: {len(leads)} New Lead{'s' if len(leads) != 1 else ''}",
                },
            },
        ]

        for lead in leads[:10]:  # Slack message size limit
            tier = lead.get("tier", "cold").upper()
            score = lead.get("lead_score", 0)
            city = lead.get("address_city", "Unknown")
            county = lead.get("county", "")
            permit = lead.get("permit_number", "N/A")
            name = lead.get("project_name") or lead.get("description", "")[:60] or "Unnamed"

            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*[{tier}] {name}*\n"
                        f"Score: {score} | {city}, {county} Co.\n"
                        f"Permit: {permit}"
                    ),
                },
            })

        return blocks


class WebhookChannel(NotificationChannel):
    """Send leads to a customer-configured webhook URL with HMAC signing."""

    channel_type = "webhook"

    async def send(self, leads: list[dict[str, Any]], config: dict[str, Any]) -> bool:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Webhook channel missing webhook_url")
            return False

        secret = config.get("secret", "")
        payload = json.dumps({"leads": leads}, default=str)
        signature = self._sign(payload, secret) if secret else ""

        headers = {
            "Content-Type": "application/json",
            "X-Landscraper-Signature": signature,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(webhook_url, content=payload, headers=headers)
            if response.status_code >= 400:
                logger.error("Webhook delivery failed: %s", response.status_code)
                return False

        logger.info("Sent %d leads to webhook %s", len(leads), webhook_url)
        return True

    @staticmethod
    def _sign(payload: str, secret: str) -> str:
        """HMAC-SHA256 signature for webhook verification."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()


class EmailChannel(NotificationChannel):
    """Send lead digest via email.

    POC: logs the email content. Production: integrate with SendGrid/SES.
    """

    channel_type = "email"

    async def send(self, leads: list[dict[str, Any]], config: dict[str, Any]) -> bool:
        to_email = config.get("email")
        if not to_email:
            logger.error("Email channel missing recipient email")
            return False

        subject = f"Landscraper: {len(leads)} New Development Lead{'s' if len(leads) != 1 else ''}"
        body = self._build_digest(leads)

        # POC: log instead of sending
        logger.info("Email to %s: %s\n%s", to_email, subject, body[:200])
        return True

    def _build_digest(self, leads: list[dict[str, Any]]) -> str:
        lines = ["Landscraper Lead Digest", "=" * 40, ""]
        for lead in leads:
            tier = lead.get("tier", "cold").upper()
            score = lead.get("lead_score", 0)
            city = lead.get("address_city", "Unknown")
            permit = lead.get("permit_number", "N/A")
            name = lead.get("project_name", "Unnamed")
            lines.append(f"[{tier}] {name} (Score: {score})")
            lines.append(f"  Location: {city} | Permit: {permit}")
            lines.append("")
        return "\n".join(lines)
