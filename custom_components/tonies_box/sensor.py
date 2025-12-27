"""Sensor platform for Toniebox."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TonieboxDataUpdateCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toniebox sensor based on a config entry."""
    coordinator: TonieboxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create sensor entities for each creative tonie
    for tonie in coordinator.data.get("creative_tonies", []):
        entities.extend(
            [
                CreativeTonieChaptersSensor(coordinator, tonie, entry),
                CreativeTonieTimeSensor(coordinator, tonie, entry),
                CreativeTonieRemainingChaptersSensor(coordinator, tonie, entry),
                CreativeTonieRemainingTimeSensor(coordinator, tonie, entry),
                CreativeTonieTranscodingSensor(coordinator, tonie, entry),
                CreativeTonieLastUpdateSensor(coordinator, tonie, entry),
            ]
        )

    async_add_entities(entities)


class CreativeTonieBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Creative Tonie sensors."""

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._tonie_id = tonie.id
        self._household_id = tonie.householdId
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._tonie_id)},
            name=tonie.name,
            manufacturer="Boxine",
            model="Creative Tonie",
            configuration_url="https://meine.tonies.de",
        )

    @property
    def _tonie(self):
        """Get the current tonie data."""
        for tonie in self.coordinator.data.get("creative_tonies", []):
            if tonie.id == self._tonie_id:
                return tonie
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self._tonie is not None


class CreativeTonieChaptersSensor(CreativeTonieBaseSensor):
    """Sensor for number of chapters present."""

    _attr_icon = "mdi:book-open-page-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Chapters"
        self._attr_unique_id = f"{tonie.id}_chapters_present"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self._tonie:
            return self._tonie.chaptersPresent
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self._tonie:
            return {}

        return {
            "chapter_list": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "seconds": chapter.seconds,
                    "transcoding": chapter.transcoding,
                }
                for chapter in self._tonie.chapters
            ],
            "total_chapters": len(self._tonie.chapters),
        }


class CreativeTonieTimeSensor(CreativeTonieBaseSensor):
    """Sensor for total time present."""

    _attr_icon = "mdi:timer"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Duration"
        self._attr_unique_id = f"{tonie.id}_seconds_present"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self._tonie:
            return self._tonie.secondsPresent
        return None


class CreativeTonieRemainingChaptersSensor(CreativeTonieBaseSensor):
    """Sensor for remaining chapters capacity."""

    _attr_icon = "mdi:book-plus"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Remaining Chapters"
        self._attr_unique_id = f"{tonie.id}_chapters_remaining"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self._tonie:
            return self._tonie.chaptersRemaining
        return None


class CreativeTonieRemainingTimeSensor(CreativeTonieBaseSensor):
    """Sensor for remaining time capacity."""

    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Remaining Duration"
        self._attr_unique_id = f"{tonie.id}_seconds_remaining"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self._tonie:
            return self._tonie.secondsRemaining
        return None


class CreativeTonieTranscodingSensor(CreativeTonieBaseSensor):
    """Sensor for transcoding status."""

    _attr_icon = "mdi:cog-sync"

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Transcoding"
        self._attr_unique_id = f"{tonie.id}_transcoding"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self._tonie:
            return "transcoding" if self._tonie.transcoding else "ready"
        return None

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._tonie and self._tonie.transcoding:
            return "mdi:cog-sync"
        return "mdi:check-circle"


class CreativeTonieLastUpdateSensor(CreativeTonieBaseSensor):
    """Sensor for last update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: TonieboxDataUpdateCoordinator,
        tonie: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tonie, entry)
        self._attr_name = f"{tonie.name} Last Update"
        self._attr_unique_id = f"{tonie.id}_last_update"

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        if self._tonie and self._tonie.lastUpdate:
            return self._tonie.lastUpdate
        return None
