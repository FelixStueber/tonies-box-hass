"""Tests for entity state calculations."""
from unittest.mock import MagicMock

import pytest

from custom_components.tonies_box.coordinator import TonieboxDataUpdateCoordinator
from custom_components.tonies_box.sensor import (
    TonieboxVolumeSensor,
    TonieboxHeadphoneVolumeSensor,
    TonieboxSSIDSensor,
    CreativeTonieChaptersSensor,
    CreativeTonieDurationSensor,
    CreativeTonieRemainingSensor,
    CreativeTonieTranscodingSensor,
)
from custom_components.tonies_box.binary_sensor import (
    TonieboxOfflineSensor,
    CreativeTonieLiveSensor,
    CreativeToniePrivateSensor,
)
from custom_components.tonies_box.switch import TonieboxEarSlapSwitch
from custom_components.tonies_box.select import TonieboxLEDSelect


MOCK_DATA = {
    "households": [{"id": "hh-1"}],
    "boxes": {
        "box-1": {
            "id": "box-1",
            "household_id": "hh-1",
            "name": "My Box",
            "maxVolume": 75,
            "maxHeadphoneVolume": 50,
            "ssid": "MyWifi",
            "offlineMode": False,
            "accelerometerEnabled": True,
            "ledLevel": "on",
        }
    },
    "creative_tonies": {
        "tonie-1": {
            "id": "tonie-1",
            "name": "Red Tonie",
            "household_id": "hh-1",
            "chapters": [{"id": "c1"}, {"id": "c2"}],
            "secondsPresent": 1200,
            "secondsRemaining": 3600,
            "transcoding": False,
            "live": True,
            "private": False,
        }
    },
    "tonies": {},
}


def make_coordinator():
    coord = MagicMock(spec=TonieboxDataUpdateCoordinator)
    coord.data = MOCK_DATA
    return coord


def test_volume_sensor_value():
    coord = make_coordinator()
    sensor = TonieboxVolumeSensor(coord, "box-1")
    assert sensor.native_value == 75


def test_headphone_volume_sensor_value():
    coord = make_coordinator()
    sensor = TonieboxHeadphoneVolumeSensor(coord, "box-1")
    assert sensor.native_value == 50


def test_ssid_sensor_value():
    coord = make_coordinator()
    sensor = TonieboxSSIDSensor(coord, "box-1")
    assert sensor.native_value == "MyWifi"


def test_offline_sensor_false():
    coord = make_coordinator()
    sensor = TonieboxOfflineSensor(coord, "box-1")
    assert sensor.is_on is False


def test_ear_slap_switch_on():
    coord = make_coordinator()
    switch = TonieboxEarSlapSwitch(coord, "box-1")
    assert switch.is_on is True


def test_led_select_current_option():
    coord = make_coordinator()
    select = TonieboxLEDSelect(coord, "box-1")
    assert select.current_option == "on"


def test_chapters_sensor_count():
    coord = make_coordinator()
    sensor = CreativeTonieChaptersSensor(coord, "tonie-1")
    assert sensor.native_value == 2


def test_duration_sensor_value():
    coord = make_coordinator()
    sensor = CreativeTonieDurationSensor(coord, "tonie-1")
    assert sensor.native_value == 1200


def test_remaining_sensor_value():
    coord = make_coordinator()
    sensor = CreativeTonieRemainingSensor(coord, "tonie-1")
    assert sensor.native_value == 3600


def test_transcoding_sensor_ready():
    coord = make_coordinator()
    sensor = CreativeTonieTranscodingSensor(coord, "tonie-1")
    assert sensor.native_value == "ready"


def test_transcoding_sensor_transcoding():
    coord = make_coordinator()
    coord.data = dict(MOCK_DATA)
    coord.data["creative_tonies"] = dict(MOCK_DATA["creative_tonies"])
    coord.data["creative_tonies"]["tonie-1"] = dict(MOCK_DATA["creative_tonies"]["tonie-1"])
    coord.data["creative_tonies"]["tonie-1"]["transcoding"] = True
    sensor = CreativeTonieTranscodingSensor(coord, "tonie-1")
    assert sensor.native_value == "transcoding"


def test_live_sensor_on():
    coord = make_coordinator()
    sensor = CreativeTonieLiveSensor(coord, "tonie-1")
    assert sensor.is_on is True


def test_private_sensor_off():
    coord = make_coordinator()
    sensor = CreativeToniePrivateSensor(coord, "tonie-1")
    assert sensor.is_on is False


from custom_components.tonies_box.sensor import (
    TonieboxBatterySensor,
    TonieboxRSSISensor,
    TonieboxLastPlayedSensor,
)


def test_battery_sensor_value():
    coord = make_coordinator()
    coord.data = dict(MOCK_DATA)
    coord.data["boxes"] = dict(MOCK_DATA["boxes"])
    coord.data["boxes"]["box-1"] = dict(MOCK_DATA["boxes"]["box-1"])
    coord.data["boxes"]["box-1"]["batteryLevel"] = 85
    sensor = TonieboxBatterySensor(coord, "box-1")
    assert sensor.native_value == 85


def test_rssi_sensor_value():
    coord = make_coordinator()
    coord.data = dict(MOCK_DATA)
    coord.data["boxes"] = dict(MOCK_DATA["boxes"])
    coord.data["boxes"]["box-1"] = dict(MOCK_DATA["boxes"]["box-1"])
    coord.data["boxes"]["box-1"]["rssi"] = -65
    sensor = TonieboxRSSISensor(coord, "box-1")
    assert sensor.native_value == -65


def test_battery_sensor_none_when_absent():
    coord = make_coordinator()
    sensor = TonieboxBatterySensor(coord, "box-1")
    assert sensor.native_value is None


def test_rssi_sensor_none_when_absent():
    coord = make_coordinator()
    sensor = TonieboxRSSISensor(coord, "box-1")
    assert sensor.native_value is None


def test_last_played_sensor_value():
    from datetime import datetime, timezone
    coord = make_coordinator()
    coord.data = dict(MOCK_DATA)
    coord.data["boxes"] = dict(MOCK_DATA["boxes"])
    coord.data["boxes"]["box-1"] = dict(MOCK_DATA["boxes"]["box-1"])
    coord.data["boxes"]["box-1"]["lastPlayed"] = "2026-05-04T10:00:00Z"
    sensor = TonieboxLastPlayedSensor(coord, "box-1")
    assert sensor.native_value == datetime(2026, 5, 4, 10, 0, 0, tzinfo=timezone.utc)


def test_last_played_sensor_none_when_absent():
    coord = make_coordinator()
    sensor = TonieboxLastPlayedSensor(coord, "box-1")
    assert sensor.native_value is None


def test_last_played_sensor_malformed_timestamp():
    """Malformed timestamp returns None without crashing."""
    coord = make_coordinator()
    coord.data = dict(MOCK_DATA)
    coord.data["boxes"] = dict(MOCK_DATA["boxes"])
    coord.data["boxes"]["box-1"] = dict(MOCK_DATA["boxes"]["box-1"])
    coord.data["boxes"]["box-1"]["lastPlayed"] = "not-a-date"
    sensor = TonieboxLastPlayedSensor(coord, "box-1")
    assert sensor.native_value is None
