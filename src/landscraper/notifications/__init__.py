"""Notification delivery: email, Slack, webhook channels."""

from .dispatcher import dispatch_notifications
from .channels import EmailChannel, SlackChannel, WebhookChannel

__all__ = ["dispatch_notifications", "EmailChannel", "SlackChannel", "WebhookChannel"]
