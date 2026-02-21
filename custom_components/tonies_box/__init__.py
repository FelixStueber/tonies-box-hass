from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TonieboxApiClient
from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Toniebox from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = TonieboxApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )
    coordinator = TonieboxDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_upload_file(call: ServiceCall):
        tonie_id = call.data.get("tonie_id")
        file_path = call.data.get("file_path")
        title = call.data.get("title")

        for coordinator in hass.data[DOMAIN].values():
            if tonie_id in coordinator.data.get("creative_tonies", {}):
                await coordinator.client.async_upload_file(tonie_id, file_path, title)
                await coordinator.async_request_refresh()
                return

        raise ValueError(f"Tonie ID {tonie_id} not found")

    if not hass.services.has_service(DOMAIN, "upload_file"):
        hass.services.async_register(DOMAIN, "upload_file", handle_upload_file)

    async def handle_add_chapter(call: ServiceCall):
        tonie_id = call.data.get("tonie_id")
        file_id = call.data.get("file_id")
        title = call.data.get("title")

        for coordinator in hass.data[DOMAIN].values():
            if tonie_id in coordinator.data.get("creative_tonies", {}):
                await coordinator.client.async_add_chapter(tonie_id, file_id, title)
                await coordinator.async_request_refresh()
                return

        raise ValueError(f"Tonie ID {tonie_id} not found")

    if not hass.services.has_service(DOMAIN, "add_chapter"):
        hass.services.async_register(DOMAIN, "add_chapter", handle_add_chapter)

    async def handle_sort_chapters(call: ServiceCall):
        tonie_id = call.data.get("tonie_id")
        chapters = call.data.get("chapters")

        for coordinator in hass.data[DOMAIN].values():
            if tonie_id in coordinator.data.get("creative_tonies", {}):
                await coordinator.client.async_sort_chapters(tonie_id, chapters)
                await coordinator.async_request_refresh()
                return

        raise ValueError(f"Tonie ID {tonie_id} not found")

    if not hass.services.has_service(DOMAIN, "sort_chapters"):
        hass.services.async_register(DOMAIN, "sort_chapters", handle_sort_chapters)

    async def handle_clear_chapters(call: ServiceCall):
        tonie_id = call.data.get("tonie_id")

        for coordinator in hass.data[DOMAIN].values():
            if tonie_id in coordinator.data.get("creative_tonies", {}):
                await coordinator.client.async_clear_chapters(tonie_id)
                await coordinator.async_request_refresh()
                return

        raise ValueError(f"Tonie ID {tonie_id} not found")

    if not hass.services.has_service(DOMAIN, "clear_chapters"):
        hass.services.async_register(DOMAIN, "clear_chapters", handle_clear_chapters)

    async def handle_set_volume(call: ServiceCall):
        box_id = call.data.get("box_id")
        volume_raw = call.data.get("volume") # Get raw value

        if volume_raw is None:
            raise ValueError("Volume must be specified for set_volume service call")

        try:
            volume = int(volume_raw)
        except ValueError as e:
            raise ValueError(f"Invalid volume value: {volume_raw}") from e

        for coordinator in hass.data[DOMAIN].values():
            if box_id in coordinator.data.get("boxes", {}):
                await coordinator.client.async_set_volume(box_id, volume)
                await coordinator.async_request_refresh()
                return

        raise ValueError(f"Toniebox ID {box_id} not found")

    if not hass.services.has_service(DOMAIN, "set_volume"):
        hass.services.async_register(DOMAIN, "set_volume", handle_set_volume)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
