"""Media player entity for Toniebox."""

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
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
    """Set up media player entities from a config entry."""
    coordinator: TonieboxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        TonieboxMediaPlayer(coordinator, box_id) for box_id in coordinator.data["boxes"]
    ]
    async_add_entities(entities)


class TonieboxMediaPlayer(TonieboxEntity, MediaPlayerEntity):
    """Media player for a Toniebox.

    Supports volume control only. Mute maps to the ear-slap (accelerometer)
    toggle — the closest physical analogue on the device. Playback control
    is not supported as the Tonie Cloud API exposes no play/pause endpoint.
    """

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.VOLUME_MUTE
    )

    @property
    def unique_id(self) -> str:
        """Return unique ID for the media player."""
        return f"{self.box_id}_media_player"

    @property
    def name(self) -> str:
        """Return name of the media player."""
        return "Media Player"

    @property
    def state(self) -> MediaPlayerState:
        """Return current playback state."""
        creative_tonies = self.coordinator.data.get("creative_tonies", {})
        for tonie in creative_tonies.values():
            if tonie.get("live"):
                return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def volume_level(self) -> float:
        """Return volume level (0.0-1.0)."""
        max_vol = self.box_data.get("maxVolume", 0)
        return max_vol / 100.0

    @property
    def is_volume_muted(self) -> bool:
        """Return True if volume is muted."""
        return not self.box_data.get("accelerometerEnabled", True)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0.0-1.0)."""
        # API only accepts 25, 50, 75, 100 - round to nearest valid value
        VALID_VOLUMES = [25, 50, 75, 100]
        target_volume = round(volume * 100)
        volume_int = min(VALID_VOLUMES, key=lambda x: abs(target_volume - x))
        await self.coordinator.client.async_set_volume(self.box_id, volume_int)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute/unmute volume."""
        await self.coordinator.client.async_set_ear_slap(self.box_id, not mute)
        await self.coordinator.async_request_refresh()
