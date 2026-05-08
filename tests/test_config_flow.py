"""Tests for the RouterOS LTE config flow."""

from unittest.mock import patch

import librouteros.exceptions
import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.routeros_lte.const import CONF_MONITORED_INTERFACES, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield


async def test_form_user(hass: HomeAssistant, mock_connect, mock_routeros_data) -> None:
    """Test the user config flow with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.routeros_lte.coordinator.RouterOSCoordinator._fetch_data",
        return_value=mock_routeros_data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.88.1",
                "port": 8728,
                "username": "admin",
                "password": "secret",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RouterOS (192.168.88.1)"
    assert result["data"] == {
        "host": "192.168.88.1",
        "port": 8728,
        "username": "admin",
        "password": "secret",
    }


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test handling of connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.routeros_lte.config_flow.librouteros.connect",
        side_effect=ConnectionRefusedError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.88.1",
                "port": 8728,
                "username": "admin",
                "password": "secret",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test handling of authentication error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.routeros_lte.config_flow.librouteros.connect",
        side_effect=librouteros.exceptions.TrapError("invalid user"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.88.1",
                "port": 8728,
                "username": "admin",
                "password": "wrong",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_options_flow_shows_interfaces(
    hass: HomeAssistant, mock_connect, mock_routeros_data
) -> None:
    """Test that the options flow shows all discovered interfaces."""
    # First create a config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.routeros_lte.coordinator.RouterOSCoordinator._fetch_data",
        return_value=mock_routeros_data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.88.1",
                "port": 8728,
                "username": "admin",
                "password": "secret",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]

    # Now open the options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_select_interfaces(
    hass: HomeAssistant, mock_connect, mock_routeros_data
) -> None:
    """Test selecting specific interfaces in options flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.routeros_lte.coordinator.RouterOSCoordinator._fetch_data",
        return_value=mock_routeros_data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.88.1",
                "port": 8728,
                "username": "admin",
                "password": "secret",
            },
        )

    entry = result["result"]

    # Open options and select only ether1
    with patch(
        "custom_components.routeros_lte.coordinator.RouterOSCoordinator._fetch_data",
        return_value=mock_routeros_data,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MONITORED_INTERFACES: ["ether1"]},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_MONITORED_INTERFACES] == ["ether1"]
