from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator # Add this import


class TonieboxEntity(CoordinatorEntity):
    """Base class for Toniebox entities."""

    _attr_has_entity_name = True
    coordinator: TonieboxDataUpdateCoordinator # Add this line

    def __init__(self, coordinator: TonieboxDataUpdateCoordinator, box_id): # Add type hint here too
        super().__init__(coordinator)
        self.box_id = box_id

    @property
    def box_data(self):
        return self.coordinator.data["boxes"][self.box_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.box_id)},
            connections={(CONNECTION_NETWORK_MAC, self.box_data.get("macAddress"))}
            if self.box_data.get("macAddress")
            else set(),
            name=self.box_data.get("name", "Toniebox"),
            manufacturer="Tonies",
            model="Toniebox",
            sw_version=self.box_data.get("firmwareVersion"),
        )


class CreativeTonieEntity(CoordinatorEntity):
    """Base class for Creative Tonie entities."""

    _attr_has_entity_name = True
    coordinator: TonieboxDataUpdateCoordinator # Add this line

    def __init__(self, coordinator: TonieboxDataUpdateCoordinator, tonie_id): # Add type hint here too
        super().__init__(coordinator)
        self.tonie_id = tonie_id

    @property
    def tonie_data(self):
        return self.coordinator.data["creative_tonies"][self.tonie_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"tonies_{self.tonie_data.get('household_id')}")},
            name="My Tonies",
            manufacturer="Tonies",
            model="Tonie Collection",
        )
