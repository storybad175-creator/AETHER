import pytest
import time
from ff_api.core.auth import JWTManager
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_token_fetch():
    jwt_manager = JWTManager()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"jwt": "new_token", "expires_in": 3600})

    with patch("aiohttp.ClientSession.post", return_value=mock_resp):
        mock_resp.__aenter__.return_value = mock_resp
        token = await jwt_manager.get_token()
        assert token == "new_token"
        assert jwt_manager._token == "new_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry():
    jwt_manager = JWTManager()
    jwt_manager._token = "old_token"
    jwt_manager._expires = time.time() - 10 # Expired

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"jwt": "refreshed_token", "expires_in": 3600})

    with patch("aiohttp.ClientSession.post", return_value=mock_resp):
        mock_resp.__aenter__.return_value = mock_resp
        token = await jwt_manager.get_token()
        assert token == "refreshed_token"
