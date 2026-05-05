"""Tests for TonieboxApiClient."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.tonies_box.api import (
    TonieboxApiClient,
    TonieboxApiClientAuthenticationError,
    TonieboxApiClientCommunicationError,
)


@pytest.fixture
def mock_session():
    session = MagicMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def client(mock_session):
    return TonieboxApiClient("user@test.com", "password123", mock_session)


async def test_token_fetched_on_first_call(client, mock_session):
    """Token is fetched when none cached."""
    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"access_token": "tok123"})
    resp.raise_for_status = MagicMock()

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=cm)

    token = await client.async_get_access_token()
    assert token == "tok123"
    assert mock_session.post.call_count == 1


async def test_token_reused_when_fresh(client, mock_session):
    """Cached token is reused when less than 4 minutes old."""
    client._token = "cached-token"
    client._token_acquired_at = time.monotonic()  # just now

    token = await client.async_get_access_token()
    assert token == "cached-token"
    assert mock_session.post.call_count == 0


async def test_token_refreshed_when_stale(client, mock_session):
    """Token is re-fetched when older than 4 minutes."""
    client._token = "old-token"
    client._token_acquired_at = time.monotonic() - 300  # 5 minutes ago

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"access_token": "new-token"})
    resp.raise_for_status = MagicMock()

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=cm)

    token = await client.async_get_access_token()
    assert token == "new-token"
    assert mock_session.post.call_count == 1


async def test_get_access_token_timeout_raises_auth_error(client, mock_session):
    """Timeout during auth raises TonieboxApiClientAuthenticationError."""
    import asyncio
    mock_session.post.side_effect = asyncio.TimeoutError()

    with pytest.raises(TonieboxApiClientAuthenticationError):
        await client.async_get_access_token()


async def test_get_access_token_connection_error_raises_auth_error(client, mock_session):
    """aiohttp error during auth raises TonieboxApiClientAuthenticationError."""
    mock_session.post.side_effect = aiohttp.ClientConnectionError()

    with pytest.raises(TonieboxApiClientAuthenticationError):
        await client.async_get_access_token()
