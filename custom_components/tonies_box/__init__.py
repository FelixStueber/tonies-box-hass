"""The Toniebox integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_CHAPTERS,
    ATTR_FILE_ID,
    ATTR_FILE_PATH,
    ATTR_TITLE,
    ATTR_TONIE_ID,
    DOMAIN,
    SERVICE_ADD_CHAPTER,
    SERVICE_CLEAR_CHAPTERS,
    SERVICE_SORT_CHAPTERS,
    SERVICE_UPLOAD_FILE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SCAN_INTERVAL = timedelta(minutes=5)

# Service schemas
SERVICE_UPLOAD_FILE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TONIE_ID): cv.string,
        vol.Required(ATTR_FILE_PATH): cv.string,
        vol.Required(ATTR_TITLE): cv.string,
    }
)

SERVICE_ADD_CHAPTER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TONIE_ID): cv.string,
        vol.Required(ATTR_FILE_ID): cv.string,
        vol.Required(ATTR_TITLE): cv.string,
    }
)

SERVICE_CLEAR_CHAPTERS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TONIE_ID): cv.string,
    }
)

SERVICE_SORT_CHAPTERS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TONIE_ID): cv.string,
        vol.Required(ATTR_CHAPTERS): list,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Toniebox from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    try:
        coordinator = TonieboxDataUpdateCoordinator(hass, username, password)
        await coordinator.async_config_entry_first_refresh()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_upload_file(call: ServiceCall) -> None:
        """Handle the upload_file service call."""
        tonie_id = call.data[ATTR_TONIE_ID]
        file_path = call.data[ATTR_FILE_PATH]
        title = call.data[ATTR_TITLE]

        tonie = _get_tonie_by_id(coordinator, tonie_id)
        if not tonie:
            raise HomeAssistantError(f"Creative Tonie with ID {tonie_id} not found")

        if not Path(file_path).exists():
            raise HomeAssistantError(f"File not found: {file_path}")

        await hass.async_add_executor_job(
            coordinator.api.upload_file_to_tonie, tonie, file_path, title
        )
        await coordinator.async_request_refresh()

    async def handle_add_chapter(call: ServiceCall) -> None:
        """Handle the add_chapter service call."""
        tonie_id = call.data[ATTR_TONIE_ID]
        file_id = call.data[ATTR_FILE_ID]
        title = call.data[ATTR_TITLE]

        tonie = _get_tonie_by_id(coordinator, tonie_id)
        if not tonie:
            raise HomeAssistantError(f"Creative Tonie with ID {tonie_id} not found")

        await hass.async_add_executor_job(
            coordinator.api.add_chapter_to_tonie, tonie, file_id, title
        )
        await coordinator.async_request_refresh()

    async def handle_clear_chapters(call: ServiceCall) -> None:
        """Handle the clear_chapters service call."""
        tonie_id = call.data[ATTR_TONIE_ID]

        tonie = _get_tonie_by_id(coordinator, tonie_id)
        if not tonie:
            raise HomeAssistantError(f"Creative Tonie with ID {tonie_id} not found")

        await hass.async_add_executor_job(
            coordinator.api.clear_all_chapter_of_tonie, tonie
        )
        await coordinator.async_request_refresh()

    async def handle_sort_chapters(call: ServiceCall) -> None:
        """Handle the sort_chapters service call."""
        from tonie_api.models import Chapter

        tonie_id = call.data[ATTR_TONIE_ID]
        chapters_data = call.data[ATTR_CHAPTERS]

        tonie = _get_tonie_by_id(coordinator, tonie_id)
        if not tonie:
            raise HomeAssistantError(f"Creative Tonie with ID {tonie_id} not found")

        chapters = [Chapter(**ch) for ch in chapters_data]
        await hass.async_add_executor_job(
            coordinator.api.sort_chapter_of_tonie, tonie, chapters
        )
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_UPLOAD_FILE, handle_upload_file, schema=SERVICE_UPLOAD_FILE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_CHAPTER, handle_add_chapter, schema=SERVICE_ADD_CHAPTER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_CHAPTERS,
        handle_clear_chapters,
        schema=SERVICE_CLEAR_CHAPTERS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SORT_CHAPTERS,
        handle_sort_chapters,
        schema=SERVICE_SORT_CHAPTERS_SCHEMA,
    )

    return True


def _get_tonie_by_id(coordinator: TonieboxDataUpdateCoordinator, tonie_id: str):
    """Get a Creative Tonie by ID."""
    for tonie in coordinator.data.get("creative_tonies", []):
        if tonie.id == tonie_id:
            return tonie
    return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AuthenticationError(Exception):
    """Authentication error."""


class TonieboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Toniebox data from the API."""

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.username = username
        self.password = password
        self.api = None
        self.api2 = None
        self._households = []

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            if self.api is None:
                # Import here to avoid blocking the event loop during startup
                from tonie_api.api import TonieAPI

                self.api = await self.hass.async_add_executor_job(
                    TonieAPI, self.username, self.password
                )
            if self.api2 is None:
                # Import here to avoid blocking the event loop during startup
                from .api import ToniesClient

                self.api2 = await self.hass.async_add_executor_job(
                    ToniesClient, self.username, self.password
                )


            # Fetch all households
            households = await self.hass.async_add_executor_job(
                self.api2.get_households
            )
            self._households = households

            # Fetch all creative tonies for all households
            creative_tonies = []
            for household in households:
                tonies = await self.hass.async_add_executor_job(
                    self.api2.get_all_creative_tonies_by_household, household
                )
                creative_tonies.extend(tonies)

            # Get user info
            user = await self.hass.async_add_executor_job(self.api2.get_me)

            return {
                "households": households,
                "creative_tonies": creative_tonies,
                "user": user,
            }

        except ValueError as err:
            raise AuthenticationError("Invalid authentication") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    @property
    def households(self):
        """Return households."""
        return self._households
