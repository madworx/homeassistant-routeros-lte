"""Tests for the RouterOS LTE config flow."""

from unittest.mock import patch

import librouteros.exceptions
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.routeros_lte.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield


async def test_form_user(hass: HomeAssistant, mock_connect) -> None:
    """Test the user config flow with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.routeros_lte.coordinator.RouterOSCoordinator._fetch_data",
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
