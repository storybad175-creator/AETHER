import pytest
import time
from unittest.mock import AsyncMock, patch
from core.auth import JWTManager
from api.errors import FFError, ErrorCode

@pytest.mark.asyncio
async def test_jwt_manager_singleton():
    manager1 = JWTManager()
    manager2 = JWTManager()
    assert manager1 is manager2

@pytest.mark.asyncio
async def test_jwt_refresh_success(mock_settings, mock_jwt):
    manager = JWTManager()
    manager._token = None # Reset

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"token": mock_jwt, "expires_in": 3600}

    with patch("core.transport.transport.session.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()
        assert token == mock_jwt
        assert manager._token == mock_jwt
        assert manager._expires_at > time.time()

@pytest.mark.asyncio
async def test_jwt_refresh_failure(mock_settings):
    manager = JWTManager()
    manager._token = None

    mock_resp = AsyncMock()
    mock_resp.status = 401

    with patch("core.transport.transport.session.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(FFError) as exc:
            await manager.refresh()
        assert exc.value.code == ErrorCode.AUTH_FAILED

@pytest.mark.asyncio
async def test_proactive_refresh(mock_settings, mock_jwt):
    manager = JWTManager()
    # Set expiry to 30 seconds in the future (within the 60s proactive window)
    manager._token = "old_token"
    manager._expires_at = time.time() + 30

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"token": "new_token", "expires_in": 3600}

    with patch("core.transport.transport.session.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_resp

        token = await manager.get_token()
        assert token == "new_token"
        mock_post.assert_called_once()
