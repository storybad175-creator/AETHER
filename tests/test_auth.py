import pytest
import aiohttp
from unittest.mock import AsyncMock, patch
from core.auth import JWTManager
from api.errors import FFError, ErrorCode

@pytest.mark.asyncio
async def test_token_fetch_success():
    jwt_manager = JWTManager()

    mock_response = {
        "access_token": "test_token",
        "expires_in": 3600
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_response
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await jwt_manager.get_token()
        assert token == "test_token"
        assert jwt_manager._token == "test_token"

@pytest.mark.asyncio
async def test_token_fetch_failure():
    jwt_manager = JWTManager()
    jwt_manager.force_refresh()

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(FFError) as exc:
            await jwt_manager.get_token()
        assert exc.value.code == ErrorCode.AUTH_FAILED
