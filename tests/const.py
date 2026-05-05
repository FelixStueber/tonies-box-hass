"""Constants for Toniebox tests."""

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tonies_box.const import DOMAIN

MOCK_CONFIG = MockConfigEntry(
    domain=DOMAIN,
    data={
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    },
)
