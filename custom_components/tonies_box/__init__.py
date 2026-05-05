from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TonieboxApiClient
from .const import DOMAIN
from .coordinator import TonieboxDataUpdateCoordinator
from .services import (
    handle_add_chapter,
    handle_clear_chapters,
    handle_set_volume,
    handle_sort_chapters,
    handle_upload_file,
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.MEDIA_PLAYER,
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

    if not hass.services.has_service(DOMAIN, "upload_file"):
        hass.services.async_register(
            DOMAIN, "upload_file", lambda call: handle_upload_file(hass, call)
        )
    if not hass.services.has_service(DOMAIN, "add_chapter"):
        hass.services.async_register(
            DOMAIN, "add_chapter", lambda call: handle_add_chapter(hass, call)
        )
    if not hass.services.has_service(DOMAIN, "sort_chapters"):
        hass.services.async_register(
            DOMAIN, "sort_chapters", lambda call: handle_sort_chapters(hass, call)
        )
    if not hass.services.has_service(DOMAIN, "clear_chapters"):
        hass.services.async_register(
            DOMAIN, "clear_chapters", lambda call: handle_clear_chapters(hass, call)
        )
    if not hass.services.has_service(DOMAIN, "set_volume"):
        hass.services.async_register(
            DOMAIN, "set_volume", lambda call: handle_set_volume(hass, call)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
