import pytest
import aiohttp
from unittest.mock import AsyncMock
from core.auth import JWTManager

@pytest.mark.asyncio
async def test_token_fetch(mock_jwt):
    manager = JWTManager()
    session = AsyncMock(spec=aiohttp.ClientSession)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"jwt": mock_jwt, "expires_in": 3600}

    session.post.return_value.__aenter__.return_value = mock_resp

    token = await manager.get_token(session)
    assert token == mock_jwt
    assert manager._token == mock_jwt
