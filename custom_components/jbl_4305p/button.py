"""Button entities for JBL 4305P."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([RediscoverInputsButton(hass, entry)])


class RediscoverInputsButton(ButtonEntity):
    """Button to trigger input rediscovery on the speaker and update HA."""

    _attr_has_entity_name = True
    _attr_name = "Rediscover Inputs"
    _attr_icon = "mdi:magnify-scan"
    _attr_unique_id: str

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_rediscover_inputs"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    async def async_press(self) -> None:
        # Call the integration service to rediscover inputs for this entry
        await self.hass.services.async_call(
            DOMAIN,
            "rediscover_inputs",
            {"entry_id": self.entry.entry_id},
            blocking=True,
        )
