"""Config flow for JBL 4305P integration."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JBL4305PClient, JBL4305PConnectionError
from .const import (
    CONF_LOG_LEVEL,
    CONF_SCAN_INTERVAL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)

LOG_LEVELS = ["debug", "info", "warning", "error"]


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    client = JBL4305PClient(data[CONF_HOST], session)

    # Test connection by getting device name
    device_name = await client.get_device_name()
    
    if not device_name:
        # Try to get player data as fallback
        player_state = await client.get_player_state()
        if player_state is None:
            raise JBL4305PConnectionError("Cannot connect to speaker")
        device_name = data.get(CONF_NAME, "JBL 4305P")

    # If user provided a name, update it on the speaker
    provided_name = data.get(CONF_NAME)
    if provided_name and provided_name.strip() and provided_name != device_name:
        try:
            await client.set_device_name(provided_name.strip())
            device_name = provided_name.strip()
        except Exception:  # pylint: disable=broad-except
            LOGGER.warning("Failed to set device name on speaker; continuing with discovered name")

    # Discover available inputs
    inputs = await client.discover_available_inputs()

    return {
        "title": device_name,
        "unique_id": data[CONF_HOST].replace(".", "_"),
        "available_inputs": inputs,
    }


class JBL4305PConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JBL 4305P."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except JBL4305PConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()

                # Store discovered inputs in data
                user_input["available_inputs"] = info["available_inputs"]

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_NAME: user_input.get(CONF_NAME, info["title"]),
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                        CONF_LOG_LEVEL: user_input.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL),
                        "available_inputs": info["available_inputs"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_NAME): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(
                        LOG_LEVELS
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> JBL4305POptionsFlow:
        """Get the options flow for this handler."""
        return JBL4305POptionsFlow(config_entry)


class JBL4305POptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for JBL 4305P."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Rediscover inputs if requested
            if user_input.get("rediscover_inputs", False):
                try:
                    session = async_get_clientsession(self.hass)
                    client = JBL4305PClient(
                        self.config_entry.data[CONF_HOST], session
                    )
                    inputs = await client.discover_available_inputs()
                    user_input["available_inputs"] = inputs
                except JBL4305PConnectionError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    LOGGER.exception("Unexpected exception during rediscovery")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(title="", data=user_input)
            else:
                # Keep existing inputs if not rediscovering
                user_input["available_inputs"] = self.config_entry.options.get(
                    "available_inputs", {}
                )
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_LOG_LEVEL,
                        default=self.config_entry.options.get(
                            CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL
                        ),
                    ): vol.In(LOG_LEVELS),
                    vol.Optional("rediscover_inputs", default=False): bool,
                }
            ),
            errors=errors,
        )
