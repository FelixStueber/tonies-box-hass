"""Tests for TonieboxDataUpdateCoordinator."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.tonies_box.api import (
    TonieboxApiClientAuthenticationError,
    TonieboxApiClientError,
)
from custom_components.tonies_box.coordinator import TonieboxDataUpdateCoordinator


MOCK_DATA = {
    "households": [{"id": "hh-1"}],
    "boxes": {"box-1": {"id": "box-1", "household_id": "hh-1", "name": "My Box"}},
    "creative_tonies": {
        "tonie-1": {"id": "tonie-1", "name": "My Tonie", "household_id": "hh-1", "chapters": []}
    },
    "tonies": {},
}


async def test_coordinator_successful_update(hass: HomeAssistant):
    """Coordinator returns data on successful API call."""
    client = MagicMock()
    client.async_get_data = AsyncMock(return_value=MOCK_DATA)

    coordinator = TonieboxDataUpdateCoordinator(hass, client)
    await coordinator.async_refresh()

    assert coordinator.data == MOCK_DATA
    assert coordinator.last_update_success is True


async def test_coordinator_auth_error_raises_update_failed(hass: HomeAssistant):
    """Auth error from API becomes UpdateFailed."""
    client = MagicMock()
    client.async_get_data = AsyncMock(
        side_effect=TonieboxApiClientAuthenticationError("bad creds")
    )

    coordinator = TonieboxDataUpdateCoordinator(hass, client)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is False


async def test_coordinator_api_error_raises_update_failed(hass: HomeAssistant):
    """Generic API error from API becomes UpdateFailed."""
    client = MagicMock()
    client.async_get_data = AsyncMock(
        side_effect=TonieboxApiClientError("network failure")
    )

    coordinator = TonieboxDataUpdateCoordinator(hass, client)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
