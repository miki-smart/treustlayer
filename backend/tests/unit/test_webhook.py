"""
Unit tests for WebhookService and webhook logic.
"""
import pytest
from app.modules.webhook.application.services.webhook_service import WebhookService

class DummyRepo:
    def __init__(self):
        self.webhooks = []
    def save(self, webhook):
        self.webhooks.append(webhook)
        return webhook
    def get_by_id(self, webhook_id):
        for w in self.webhooks:
            if w.id == webhook_id:
                return w
        return None

def test_register_webhook_assigns_id():
    repo = DummyRepo()
    service = WebhookService(repo)
    webhook = service.register_webhook(
        url="https://webhook.site/abc",
        event="user.created"
    )
    assert webhook.id is not None
    assert repo.get_by_id(webhook.id) == webhook

def test_trigger_webhook_marks_triggered():
    repo = DummyRepo()
    service = WebhookService(repo)
    webhook = service.register_webhook(
        url="https://webhook.site/abc",
        event="user.created"
    )
    service.trigger_webhook(webhook.id, payload={"foo": "bar"})
    assert webhook.last_payload == {"foo": "bar"}
