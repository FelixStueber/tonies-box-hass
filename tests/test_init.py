"""Test the Toniebox integration."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


from .const import MOCK_CONFIG


async def test_load_unload_config_entry(hass: HomeAssistant) -> None:
    """Test the Toniebox configuration entry loading/unloading."""
    config_entry = MOCK_CONFIG
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.tonies_box.TonieboxApiClient.async_get_data",
        return_value={"households": [], "boxes": {}, "creative_tonies": {}, "tonies": {}},
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED
