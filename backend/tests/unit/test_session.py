"""
Unit tests for SessionService and session logic.
"""
import pytest
from app.modules.session.application.services.session_service import SessionService

class DummyRepo:
    def __init__(self):
        self.sessions = []
    def save(self, session):
        self.sessions.append(session)
        return session
    def get_by_id(self, session_id):
        for s in self.sessions:
            if s.id == session_id:
                return s
        return None

def test_create_session_assigns_id():
    repo = DummyRepo()
    service = SessionService(repo)
    session = service.create_session(user_id="user-1")
    assert session.id is not None
    assert repo.get_by_id(session.id) == session

def test_invalidate_session_sets_flag():
    repo = DummyRepo()
    service = SessionService(repo)
    session = service.create_session(user_id="user-1")
    service.invalidate_session(session.id)
    assert session.invalidated is True
