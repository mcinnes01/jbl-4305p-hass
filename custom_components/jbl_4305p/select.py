"""Select platform for JBL 4305P."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import JBL4305PDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL 4305P select entities."""
    coordinator: JBL4305PDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    client = hass.data[DOMAIN][entry.entry_id]["client"]

    # Get available inputs from options
    available_inputs = entry.options.get("available_inputs", {})

    if not available_inputs:
        # Fallback: discover inputs if none stored
        LOGGER.warning("No inputs found in config, discovering...")
        available_inputs = await client.discover_available_inputs()

    async_add_entities([JBL4305PInputSelect(coordinator, client, entry, available_inputs)])


class JBL4305PInputSelect(CoordinatorEntity[JBL4305PDataUpdateCoordinator], SelectEntity):
    """Representation of a JBL 4305P input select."""

    _attr_has_entity_name = True
    _attr_name = "Input Source"
    _attr_icon = "mdi:speaker"

    def __init__(
        self,
        coordinator: JBL4305PDataUpdateCoordinator,
        client: Any,
        entry: ConfigEntry,
        available_inputs: dict[str, dict[str, Any]],
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._available_inputs = available_inputs
        self._attr_unique_id = f"{entry.entry_id}_input_source"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    @property
    def options(self) -> list[str]:
        """Return list of available input options."""
        return [info["name"] for info in self._available_inputs.values()] or ["Google Cast", "Bluetooth"]

    @property
    def current_option(self) -> str | None:
        """Return the current selected input."""
        data = self.coordinator.data or {}
        current_input_id = data.get("current_input")

        if not current_input_id:
            return None

        # Find the input info by ID
        input_info = self._available_inputs.get(current_input_id)
        return input_info["name"] if input_info else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected input."""
        # Find the input ID by name
        input_info = None

        for _inp_id, info in self._available_inputs.items():
            if info["name"] == option:
                input_info = info
                break

        if not input_info:
            LOGGER.error("Unknown input option: %s", option)
            return

        service_id = input_info["service_id"]
        device_path = input_info.get("device_path")

        LOGGER.info("Switching to input: %s (service: %s)", option, service_id)

        success = await self._client.switch_input(service_id, device_path)

        if success:
            # Update coordinator data
            await self.coordinator.async_request_refresh()
        else:
            LOGGER.error("Failed to switch input to: %s", option)
