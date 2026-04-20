import pytest
from unittest.mock import AsyncMock, patch
from core.auth import JWTManager

@pytest.mark.asyncio
async def test_token_fetch(mock_settings):
    manager = JWTManager()

    mock_resp = AsyncMock()
    mock_resp.__aenter__.return_value.status = 200
    mock_resp.__aenter__.return_value.json.return_value = {"jwt": "new.token", "expires_in": 3600}

    with patch("core.transport.transport.session.post", return_value=mock_resp):
        token = await manager.get_token()
        assert token == "new.token"
        assert manager._token == "new.token"

@pytest.mark.asyncio
async def test_token_caching(mock_settings):
    manager = JWTManager()
    manager._token = "cached.token"
    manager._expires_at = 9999999999 # Far in the future

    token = await manager.get_token()
    assert token == "cached.token"

@pytest.mark.asyncio
async def test_force_refresh(mock_settings):
    manager = JWTManager()
    manager._token = "cached.token"
    manager._expires_at = 9999999999

    manager.force_refresh()
    assert manager._token is None
    assert manager._expires_at == 0
