"""
Domain and HTTP exception types for TrustLayer ID.
"""
from fastapi import HTTPException, status


class DomainError(Exception):
    """Base domain exception."""


class BadRequestError(DomainError):
    """Invalid input or business rule violation (maps to HTTP 400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, resource: str, identifier: str = ""):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg)
        self.resource = resource
        self.identifier = identifier


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class InvalidOperationError(DomainError):
    pass


def http_not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def http_conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def http_unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_forbidden(detail: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def http_bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
