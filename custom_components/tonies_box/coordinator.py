from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    TonieboxApiClient,
    TonieboxApiClientAuthenticationError,
    TonieboxApiClientError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class TonieboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Toniebox data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TonieboxApiClient,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            return await self.client.async_get_data()
        except TonieboxApiClientAuthenticationError as exception:
            raise UpdateFailed(exception) from exception
        except TonieboxApiClientError as exception:
            raise UpdateFailed(exception) from exception