import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.auth import JWTManager

@pytest.mark.asyncio
async def test_token_fetch():
    manager = JWTManager()
    session = MagicMock()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"jwt": "new_token", "expires_in": 3600})
    session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    session.post.side_effect = None
    session.post.return_value = session.post.return_value # Ensure it's not a coroutine

    token = await manager.get_token(session)
    assert token == "new_token"
    assert manager._token == "new_token"

@pytest.mark.asyncio
async def test_token_refresh_on_expiry():
    manager = JWTManager()
    manager._token = "old_token"
    manager._expires = 0 # Expired

    session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"jwt": "refreshed_token", "expires_in": 3600})
    session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

    token = await manager.get_token(session)
    assert token == "refreshed_token"
