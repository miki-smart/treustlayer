"""
Unit tests for AppRegistryService and app registration logic.
"""
import pytest
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService

class DummyRepo:
    def __init__(self):
        self.apps = []
    def save(self, app):
        self.apps.append(app)
        return app
    def get_by_client_id(self, client_id):
        for app in self.apps:
            if app.client_id == client_id:
                return app
        return None

def test_register_app_assigns_client_id():
    repo = DummyRepo()
    service = AppRegistryService(repo)
    app = service.register_app(
        name="TestApp",
        allowed_scopes=["openid"],
        redirect_uris=["https://cb"],
        description="desc"
    )
    assert app.client_id is not None
    assert repo.get_by_client_id(app.client_id) == app

def test_approve_app_sets_approved():
    repo = DummyRepo()
    service = AppRegistryService(repo)
    app = service.register_app(
        name="TestApp",
        allowed_scopes=["openid"],
        redirect_uris=["https://cb"],
        description="desc"
    )
    service.approve_app(app.client_id)
    assert app.approved is True
