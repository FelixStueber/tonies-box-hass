"""Tests for TonieboxMediaPlayer."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.media_player import MediaPlayerState

from custom_components.tonies_box.coordinator import TonieboxDataUpdateCoordinator
from custom_components.tonies_box.media_player import TonieboxMediaPlayer


MOCK_DATA_PLAYING = {
    "boxes": {
        "box-1": {
            "id": "box-1",
            "household_id": "hh-1",
            "name": "My Box",
            "maxVolume": 80,
            "accelerometerEnabled": True,
        }
    },
    "creative_tonies": {
        "tonie-1": {
            "id": "tonie-1",
            "name": "Red Tonie",
            "household_id": "hh-1",
            "live": True,
            "chapters": [{"id": "c1", "title": "Chapter One"}],
        }
    },
    "tonies": {},
}

MOCK_DATA_IDLE = {
    "boxes": {
        "box-1": {
            "id": "box-1",
            "household_id": "hh-1",
            "name": "My Box",
            "maxVolume": 50,
            "accelerometerEnabled": False,
        }
    },
    "creative_tonies": {
        "tonie-1": {
            "id": "tonie-1",
            "name": "Red Tonie",
            "household_id": "hh-1",
            "live": False,
            "chapters": [],
        }
    },
    "tonies": {},
}


def make_coordinator(data):
    coord = MagicMock(spec=TonieboxDataUpdateCoordinator)
    coord.data = data
    coord.client = MagicMock()
    coord.client.async_set_volume = AsyncMock()
    coord.client.async_set_ear_slap = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


def test_state_playing_when_live():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")
    assert player.state == MediaPlayerState.PLAYING


def test_state_idle_when_not_live():
    coord = make_coordinator(MOCK_DATA_IDLE)
    player = TonieboxMediaPlayer(coord, "box-1")
    assert player.state == MediaPlayerState.IDLE


def test_volume_level_normalised():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")
    assert player.volume_level == pytest.approx(0.8)


def test_is_volume_muted_false_when_ear_slap_on():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")
    assert player.is_volume_muted is False


def test_unique_id():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")
    assert player.unique_id == "box-1_media_player"


async def test_set_volume_level_converts_and_refreshes():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")

    await player.async_set_volume_level(0.75)

    coord.client.async_set_volume.assert_called_once_with("box-1", 75)
    coord.async_request_refresh.assert_called_once()


async def test_mute_volume_calls_ear_slap_and_refreshes():
    coord = make_coordinator(MOCK_DATA_PLAYING)
    player = TonieboxMediaPlayer(coord, "box-1")

    await player.async_mute_volume(True)

    # mute=True means ear_slap disabled (not mute) = False
    coord.client.async_set_ear_slap.assert_called_once_with("box-1", False)
    coord.async_request_refresh.assert_called_once()
