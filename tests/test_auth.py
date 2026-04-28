import pytest
import time
from unittest.mock import AsyncMock, patch
from core.auth import JWTManager
from api.errors import FFError, ErrorCode

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    manager = JWTManager()

    mock_resp_data = {"jwt": "new_token", "expires_in": 3600}

    with patch("core.transport.transport.session.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_resp_data
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()

        assert token == "new_token"
        assert manager._token == "new_token"
        assert manager._expires_at > time.time()

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_settings):
    manager = JWTManager()
    manager._token = "old_token"
    manager._expires_at = time.time() - 10 # Already expired

    mock_resp_data = {"jwt": "refreshed_token", "expires_in": 3600}

    with patch("core.transport.transport.session.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_resp_data
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()

        assert token == "refreshed_token"
        assert mock_post.called

@pytest.mark.asyncio
async def test_major_login_failure(mock_settings):
    manager = JWTManager()

    with patch("core.transport.transport.session.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(FFError) as exc:
            await manager.get_token()

        assert exc.value.code == ErrorCode.AUTH_FAILED
