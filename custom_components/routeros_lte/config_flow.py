"""Config flow for MikroTik RouterOS LTE integration."""

import librouteros
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_HOST,
    CONF_MONITORED_INTERFACES,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_PORT,
    DOMAIN,
)


class RouterOSLTEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RouterOS LTE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, str] = {}
        self._interfaces: list[str] = []

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RouterOSOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                interfaces = await self._test_connection(user_input)
            except librouteros.exceptions.TrapError:
                errors["base"] = "invalid_auth"
            except (ConnectionRefusedError, OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                self._user_input = user_input
                self._interfaces = interfaces
                return await self.async_step_select_interfaces()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_USERNAME, default="admin"): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_interfaces(
        self, user_input: dict[str, list[str]] | None = None
    ) -> ConfigFlowResult:
        """Handle interface selection step."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"RouterOS ({self._user_input[CONF_HOST]})",
                data=self._user_input,
                options={
                    CONF_MONITORED_INTERFACES: user_input[CONF_MONITORED_INTERFACES]
                },
            )

        return self.async_show_form(
            step_id="select_interfaces",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MONITORED_INTERFACES,
                        default=self._interfaces,
                    ): vol.All(
                        cv.multi_select(
                            {name: name for name in self._interfaces}
                        ),
                    ),
                }
            ),
        )

    async def _test_connection(self, user_input: dict[str, str]) -> list[str]:
        """Test connection and return list of interface names."""

        def _connect() -> list[str]:
            api = librouteros.connect(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                port=user_input[CONF_PORT],
            )
            try:
                interfaces = list(api("/interface/print"))
                return [iface.get("name", "") for iface in interfaces if iface.get("name")]
            finally:
                api.close()

        return await self.hass.async_add_executor_job(_connect)


class RouterOSOptionsFlow(OptionsFlow):
    """Handle options for RouterOS LTE."""

    async def async_step_init(
        self, user_input: dict[str, list[str]] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
        all_interfaces = [iface["name"] for iface in coordinator.data.interfaces]

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_MONITORED_INTERFACES, all_interfaces
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MONITORED_INTERFACES,
                        default=current,
                    ): vol.All(
                        cv.multi_select({name: name for name in all_interfaces}),
                    ),
                }
            ),
        )
