import asyncio
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


async def _idle(*args, **kwargs):
    """Replace background tasks so they never open a real RabbitMQ connection."""
    await asyncio.Event().wait()


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
}), patch("src.dispatcher.initial_dispatcher", new=_idle), \
     patch("src.dispatcher.result_collector", new=_idle):
    from src.main import app


@pytest.fixture
def client():
    """Test client"""
    with TestClient(app) as client:
        yield client
