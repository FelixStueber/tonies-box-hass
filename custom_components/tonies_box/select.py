from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import cast  # Add this import

from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator
from .entity import TonieboxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toniebox selects."""
    coordinator = cast(TonieboxDataUpdateCoordinator, hass.data[DOMAIN][entry.entry_id])

    entities = []

    for box_id in coordinator.data["boxes"]:
        entities.append(TonieboxLEDSelect(coordinator, box_id))

    async_add_entities(entities)


class TonieboxLEDSelect(TonieboxEntity, SelectEntity):
    """Select entity for Toniebox LED."""

    _attr_options = ["off", "dimmed", "on"]

    @property
    def unique_id(self):
        return f"{self.box_id}_led"

    @property
    def name(self):
        return "LED"

    @property
    def current_option(self):
        return self.box_data.get("ledLevel")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.client.async_set_led(self.box_id, option)
        await self.coordinator.async_request_refresh()
