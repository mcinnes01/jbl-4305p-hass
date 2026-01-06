"""Test fixtures for JBL 4305P tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for API tests."""
    session = MagicMock()
    response = AsyncMock()
    session.get.return_value.__aenter__.return_value = response
    return session, response
