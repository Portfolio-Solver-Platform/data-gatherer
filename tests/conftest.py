import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

with patch.dict(os.environ, {
    "RABBITMQ_HOST": "localhost",
    "RABBITMQ_PORT": "5672",
    "RABBITMQ_USER": "guest",
    "RABBITMQ_PASSWORD": "guest",
    "PROJECT_ID": "test-project",
    "CONTROL_QUEUE": "test-control-queue",
    "DIRECTOR_QUEUE": "test-director-queue",
    "PROJECT_SOLVER_RESULT_QUEUE": "test-result-queue",
    "SOLVER_DIRECTOR_RESULT_QUEUE": "test-director-result-queue",
}):
    from src.main import app


@pytest.fixture
def client():
    """Test client"""
    with TestClient(app) as client:
        yield client
