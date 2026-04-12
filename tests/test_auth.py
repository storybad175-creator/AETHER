import pytest
import aiohttp
from unittest.mock import AsyncMock, patch
from core.auth import JWTManager

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    manager = JWTManager()
    manager.force_refresh()

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600
    }

    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.post.return_value.__aenter__.return_value = mock_response

    token = await manager.get_token(mock_session)
    assert token == "new_token"
    assert manager._token == "new_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_settings):
    manager = JWTManager()
    manager._token = "old_token"
    manager._expires_at = 0.0 # Expired

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "access_token": "refreshed_token",
        "expires_in": 3600
    }

    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.post.return_value.__aenter__.return_value = mock_response

    token = await manager.get_token(mock_session)
    assert token == "refreshed_token"
