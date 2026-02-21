from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator
from .entity import TonieboxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toniebox switches."""
    coordinator: TonieboxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for box_id in coordinator.data["boxes"]:
        entities.append(TonieboxEarSlapSwitch(coordinator, box_id))

    async_add_entities(entities)


class TonieboxEarSlapSwitch(TonieboxEntity, SwitchEntity):
    """Switch for Toniebox Ear Slap."""

    @property
    def unique_id(self):
        return f"{self.box_id}_ear_slap"

    @property
    def name(self):
        return "Ear Slap"

    @property
    def is_on(self):
        return self.box_data.get("accelerometerEnabled", True)

    async def async_turn_on(self, **kwargs):
        """Turn the Ear Slap on."""
        await self.coordinator.client.async_set_ear_slap(self.box_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the Ear Slap off."""
        await self.coordinator.client.async_set_ear_slap(self.box_id, False)
        await self.coordinator.async_request_refresh()
