from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator
from .entity import CreativeTonieEntity, TonieboxEntity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toniebox sensors."""
    coordinator: TonieboxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Create raw data sensor
    entities.append(TonieboxRawDataSensor(coordinator, entry.entry_id))

    # Create entities for each Toniebox
    for box_id, box_data in coordinator.data["boxes"].items():
        entities.append(TonieboxVolumeSensor(coordinator, box_id))
        entities.append(TonieboxHeadphoneVolumeSensor(coordinator, box_id))
        entities.append(TonieboxSSIDSensor(coordinator, box_id))

    # Create entities for each Creative Tonie
    for tonie_id, tonie_data in coordinator.data["creative_tonies"].items():
        entities.append(CreativeTonieChaptersSensor(coordinator, tonie_id))
        entities.append(CreativeTonieDurationSensor(coordinator, tonie_id))
        entities.append(CreativeTonieRemainingSensor(coordinator, tonie_id))
        entities.append(CreativeTonieTranscodingSensor(coordinator, tonie_id))

    # Create entities for other Tonies
    if "tonies" in coordinator.data:
        for tonie_id, tonie_data in coordinator.data["tonies"].items():
            if tonie_id not in coordinator.data["creative_tonies"]:
                entities.append(TonieSensor(coordinator, tonie_id))

    async_add_entities(entities)

class CreativeTonieBaseSensor(CreativeTonieEntity):
    """Base class for Creative Tonie sensors."""

    @property
    def entity_picture(self):
        """Return the image URL of the Tonie."""
        return self.tonie_data.get("imageUrl")

class TonieboxRawDataSensor(CoordinatorEntity, SensorEntity):
    """Sensor to expose raw API data."""

    _attr_has_entity_name = True
    _attr_name = "Raw Data"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_raw_data"

    @property
    def native_value(self):
        """Return the total count of items as state."""
        data = self.coordinator.data
        count = 0
        if "boxes" in data:
            count += len(data["boxes"])
        if "creative_tonies" in data:
            count += len(data["creative_tonies"])
        if "tonies" in data:
            count += len(data["tonies"])
        return count

    @property
    def extra_state_attributes(self):
        """Return the raw data."""
        return self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        if "boxes" in self.coordinator.data and self.coordinator.data["boxes"]:
            box_id = next(iter(self.coordinator.data["boxes"]))
            box_data = self.coordinator.data["boxes"][box_id]
            return DeviceInfo(
                identifiers={(DOMAIN, box_id)},
                connections={(CONNECTION_NETWORK_MAC, box_data.get("macAddress"))} if box_data.get("macAddress") else set(),
                name=box_data.get("name", "Toniebox"),
                manufacturer="Tonies",
                model="Toniebox",
                sw_version=box_data.get("firmwareVersion"),
            )
        return None

class TonieboxBaseSensor(TonieboxEntity):
    """Base class for Toniebox sensors."""

    @property
    def entity_picture(self):
        """Return the image URL of the Toniebox."""
        return self.box_data.get("imageUrl")

class CreativeTonieChaptersSensor(CreativeTonieBaseSensor, SensorEntity):
    """Sensor for number of chapters."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_chapters"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Chapters"

    @property
    def native_value(self):
        return len(self.tonie_data.get("chapters", []))

class CreativeTonieDurationSensor(CreativeTonieBaseSensor, SensorEntity):
    """Sensor for duration."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_duration"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Duration"

    @property
    def native_unit_of_measurement(self):
        return "s"

    @property
    def native_value(self):
        return self.tonie_data.get("secondsPresent", 0)

class CreativeTonieRemainingSensor(CreativeTonieBaseSensor, SensorEntity):
    """Sensor for remaining duration."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_remaining"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Remaining"

    @property
    def native_unit_of_measurement(self):
        return "s"

    @property
    def native_value(self):
        return self.tonie_data.get("secondsRemaining", 0)

class CreativeTonieTranscodingSensor(CreativeTonieBaseSensor, SensorEntity):
    """Sensor for transcoding status."""

    @property
    def unique_id(self):
        return f"{self.tonie_id}_transcoding"

    @property
    def name(self):
        return f"{self.tonie_data.get('name')} Transcoding"

    @property
    def translation_key(self):
        return "transcoding"

    @property
    def native_value(self):
        if self.tonie_data.get("transcoding"):
            return "transcoding"
        return "ready"

class TonieboxVolumeSensor(TonieboxBaseSensor, SensorEntity):
    """Sensor for Toniebox maximum volume."""

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:volume-high"

    @property
    def unique_id(self):
        return f"{self.box_id}_max_volume"

    @property
    def name(self):
        return "Max Volume"

    @property
    def native_value(self):
        return self.box_data.get("maxVolume")

class TonieboxHeadphoneVolumeSensor(TonieboxBaseSensor, SensorEntity):
    """Sensor for Toniebox maximum headphone volume."""

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:headphones"

    @property
    def unique_id(self):
        return f"{self.box_id}_max_headphone_volume"

    @property
    def name(self):
        return "Max Headphone Volume"

    @property
    def native_value(self):
        return self.box_data.get("maxHeadphoneVolume")

class TonieboxSSIDSensor(TonieboxBaseSensor, SensorEntity):
    """Sensor for Toniebox SSID."""

    _attr_icon = "mdi:wifi"

    @property
    def unique_id(self):
        return f"{self.box_id}_ssid"

    @property
    def name(self):
        return "SSID"

    @property
    def native_value(self):
        return self.box_data.get("ssid")

class TonieSensor(CoordinatorEntity, SensorEntity):
    """Representation of a generic Tonie."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, tonie_id):
        super().__init__(coordinator)
        self.tonie_id = tonie_id

    @property
    def tonie_data(self):
        return self.coordinator.data["tonies"][self.tonie_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"tonies_{self.tonie_data.get('household_id')}")},
            name="My Tonies",
            manufacturer="Tonies",
            model="Tonie Collection",
        )

    @property
    def unique_id(self):
        return f"{self.tonie_id}_info"

    @property
    def name(self):
        return self.tonie_data.get("name", "Tonie")

    @property
    def native_value(self):
        return self.tonie_data.get("series", "Unknown")

    @property
    def entity_picture(self):
        """Return the image URL of the Tonie."""
        return self.tonie_data.get("imageUrl")