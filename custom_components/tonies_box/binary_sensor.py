from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator
from .entity import CreativeTonieEntity, TonieboxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toniebox binary sensors."""
    coordinator: TonieboxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for box_id in coordinator.data["boxes"]:
        entities.append(TonieboxOfflineSensor(coordinator, box_id))

    for tonie_id, tonie_data in coordinator.data["creative_tonies"].items():
        entities.append(CreativeTonieLiveSensor(coordinator, tonie_id))
        entities.append(CreativeToniePrivateSensor(coordinator, tonie_id))

    async_add_entities(entities)


class TonieboxOfflineSensor(TonieboxEntity, BinarySensorEntity):
    """Binary sensor for Toniebox offline mode."""

    @property
    def unique_id(self):
        return f"{self.box_id}_offline_mode"

    @property
    def name(self):
        return "Offline Mode"

    @property
    def is_on(self):
        return self.box_data.get("offlineMode", False)


class CreativeTonieBinarySensorBase(CreativeTonieEntity, BinarySensorEntity):
    """Base class for Creative Tonie binary sensors."""


class CreativeTonieLiveSensor(CreativeTonieBinarySensorBase):
    """Binary sensor for Creative Tonie Live status."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_live"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Live"

    @property
    def is_on(self):
        return self.tonie_data.get("live", False)


class CreativeToniePrivateSensor(CreativeTonieBinarySensorBase):
    """Binary sensor for Creative Tonie Private status."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_private"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Private"

    @property
    def is_on(self):
        return self.tonie_data.get("private", False)
