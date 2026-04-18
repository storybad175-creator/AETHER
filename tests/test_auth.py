import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from core.auth import JWTManager

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    jwt_manager = JWTManager()
    jwt_manager._token = None # Reset

    mock_transport = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"jwt": "new_token", "expires_in": 3600}

    mock_transport.session.post.return_value.__aenter__.return_value = mock_resp

    token = await jwt_manager.get_token(mock_transport)
    assert token == "new_token"
    assert jwt_manager._token == "new_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_settings):
    jwt_manager = JWTManager()
    jwt_manager._token = "old_token"
    jwt_manager._expires_at = time.time() - 10 # Expired

    mock_transport = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"jwt": "refreshed_token", "expires_in": 3600}
    mock_transport.session.post.return_value.__aenter__.return_value = mock_resp

    token = await jwt_manager.get_token(mock_transport)
    assert token == "refreshed_token"
