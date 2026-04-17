import pytest
import time
from unittest.mock import patch, AsyncMock
from core.auth import JWTManager
from api.errors import FFError

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    manager = JWTManager()
    manager._token = None # Reset

    mock_response_data = {"jwt": "new_token", "expires_in": 3600}

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_response_data
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()
        assert token == "new_token"
        assert manager._token == "new_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_settings):
    manager = JWTManager()
    manager._token = "old_token"
    manager._expires_at = time.time() - 10 # Expired

    mock_response_data = {"jwt": "refreshed_token", "expires_in": 3600}

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_response_data
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()
        assert token == "refreshed_token"

@pytest.mark.asyncio
async def test_auth_failed(mock_settings):
    manager = JWTManager()
    manager._token = None

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(FFError) as excinfo:
            await manager.get_token()
        assert "AUTH_FAILED" in str(excinfo.value.code)
