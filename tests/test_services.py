"""Tests for service handlers."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError

from custom_components.tonies_box.services import (
    handle_upload_file,
    handle_add_chapter,
    handle_sort_chapters,
    handle_clear_chapters,
    handle_set_volume,
)


def make_coordinator(data):
    coord = MagicMock()
    coord.data = data
    coord.client = MagicMock()
    coord.client.async_upload_file = AsyncMock()
    coord.client.async_add_chapter = AsyncMock()
    coord.client.async_sort_chapters = AsyncMock()
    coord.client.async_clear_chapters = AsyncMock()
    coord.client.async_set_volume = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


MOCK_DATA = {
    "creative_tonies": {
        "tonie-1": {"household_id": "hh-1", "chapters": []},
    },
    "boxes": {
        "box-1": {"household_id": "hh-1"},
    },
}


async def test_upload_file_valid_tonie(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "tonie-1", "file_path": "/tmp/test.mp3", "title": "My Track"}

    await handle_upload_file(hass, call)

    coordinator.client.async_upload_file.assert_called_once_with("tonie-1", "/tmp/test.mp3", "My Track")
    coordinator.async_request_refresh.assert_called_once()


async def test_upload_file_invalid_tonie_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "unknown-tonie", "file_path": "/tmp/test.mp3", "title": "My Track"}

    with pytest.raises(ServiceValidationError):
        await handle_upload_file(hass, call)


async def test_upload_file_makes_no_extra_api_calls(hass: HomeAssistant):
    """Service must use coordinator cache, not call async_get_data."""
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "tonie-1", "file_path": "/tmp/test.mp3", "title": "My Track"}

    await handle_upload_file(hass, call)

    coordinator.client.async_get_data = MagicMock()  # should never be called
    coordinator.client.async_get_data.assert_not_called()


async def test_set_volume_valid_box(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"box_id": "box-1", "volume": 80}

    await handle_set_volume(hass, call)

    coordinator.client.async_set_volume.assert_called_once_with("box-1", 80)
    coordinator.async_request_refresh.assert_called_once()


async def test_set_volume_missing_volume_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"box_id": "box-1", "volume": None}

    with pytest.raises(ServiceValidationError):
        await handle_set_volume(hass, call)


async def test_set_volume_invalid_box_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"box_id": "unknown-box", "volume": 80}

    with pytest.raises(ServiceValidationError):
        await handle_set_volume(hass, call)


async def test_clear_chapters_valid(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "tonie-1"}

    await handle_clear_chapters(hass, call)

    coordinator.client.async_clear_chapters.assert_called_once_with("tonie-1")
    coordinator.async_request_refresh.assert_called_once()


async def test_add_chapter_valid(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "tonie-1", "file_id": "file-abc", "title": "Chapter 1"}

    await handle_add_chapter(hass, call)

    coordinator.client.async_add_chapter.assert_called_once_with("tonie-1", "file-abc", "Chapter 1")
    coordinator.async_request_refresh.assert_called_once()


async def test_sort_chapters_valid(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "tonie-1", "chapters": [{"id": "c1"}, {"id": "c2"}]}

    await handle_sort_chapters(hass, call)

    coordinator.client.async_sort_chapters.assert_called_once_with("tonie-1", [{"id": "c1"}, {"id": "c2"}])
    coordinator.async_request_refresh.assert_called_once()


async def test_add_chapter_invalid_tonie_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "unknown-tonie", "file_id": "file-abc", "title": "Chapter 1"}

    with pytest.raises(ServiceValidationError):
        await handle_add_chapter(hass, call)


async def test_sort_chapters_invalid_tonie_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "unknown-tonie", "chapters": []}

    with pytest.raises(ServiceValidationError):
        await handle_sort_chapters(hass, call)


async def test_clear_chapters_invalid_tonie_raises(hass: HomeAssistant):
    coordinator = make_coordinator(MOCK_DATA)
    hass.data["tonies_box"] = {"entry-1": coordinator}

    call = MagicMock(spec=ServiceCall)
    call.data = {"tonie_id": "unknown-tonie"}

    with pytest.raises(ServiceValidationError):
        await handle_clear_chapters(hass, call)
