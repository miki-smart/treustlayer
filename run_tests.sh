#!/bin/bash
# TrustLayer ID - Test Runner Script
# Runs all unit and integration tests for backend and frontend

set -e

echo "=========================================="
echo "TrustLayer ID - Test Suite Runner"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend Tests
echo -e "${YELLOW}Running Backend Tests...${NC}"
echo ""

cd backend-merged

echo "Installing backend test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock

echo ""
echo "Running backend unit tests..."
pytest tests/unit -v --cov=app --cov-report=term-missing --cov-report=html:../coverage/backend

BACKEND_EXIT_CODE=$?

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend unit tests passed${NC}"
else
    echo -e "${RED}✗ Backend unit tests failed${NC}"
fi

echo ""
echo "Running backend integration tests..."
pytest tests/integration -v

BACKEND_INTEGRATION_EXIT_CODE=$?

if [ $BACKEND_INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend integration tests passed${NC}"
else
    echo -e "${RED}✗ Backend integration tests failed${NC}"
fi

cd ..

echo ""
echo "=========================================="

# Frontend Tests
echo -e "${YELLOW}Running Frontend Tests...${NC}"
echo ""

cd frontend

echo "Installing frontend test dependencies..."
npm install --silent

echo ""
echo "Running frontend tests..."
npm test -- --coverage --reporter=verbose

FRONTEND_EXIT_CODE=$?

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}"
else
    echo -e "${RED}✗ Frontend tests failed${NC}"
fi

cd ..

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Backend Unit Tests: FAILED${NC}"
fi

if [ $BACKEND_INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend Integration Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Backend Integration Tests: FAILED${NC}"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Frontend Tests: FAILED${NC}"
fi

echo ""
echo "Coverage reports generated:"
echo "  - Backend: coverage/backend/index.html"
echo "  - Frontend: frontend/coverage/index.html"
echo ""

# Exit with error if any tests failed
if [ $BACKEND_EXIT_CODE -ne 0 ] || [ $BACKEND_INTEGRATION_EXIT_CODE -ne 0 ] || [ $FRONTEND_EXIT_CODE -ne 0 ]; then
    exit 1
fi

echo -e "${GREEN}All tests passed successfully!${NC}"
exit 0
