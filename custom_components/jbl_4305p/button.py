"""Button entities for JBL 4305P."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import JBL4305PDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        RediscoverInputsButton(hass, entry),
        SwitchToGoogleCastButton(hass, entry),
        SwitchToLastBluetoothButton(hass, entry),
        AddCurrentBluetoothButton(hass, entry),
    ])


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


class SwitchToGoogleCastButton(ButtonEntity):
    """Button to switch input to Google Cast."""

    _attr_has_entity_name = True
    _attr_name = "Switch to Google Cast"
    _attr_icon = "mdi:cast"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_switch_googlecast"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    async def async_press(self) -> None:
        client = self.hass.data[DOMAIN][self.entry.entry_id]["client"]
        await client.switch_input("googlecast")


class SwitchToLastBluetoothButton(ButtonEntity):
    """Button to switch input to last seen Bluetooth device."""

    _attr_has_entity_name = True
    _attr_name = "Switch to Bluetooth (last)"
    _attr_icon = "mdi:bluetooth"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_switch_bluetooth_last"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    async def async_press(self) -> None:
        client = self.hass.data[DOMAIN][self.entry.entry_id]["client"]
        coordinator: JBL4305PDataUpdateCoordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        last_path = (coordinator.data or {}).get("last_bt_device_path")
        await client.switch_input("bluetooth", device_path=last_path)


class AddCurrentBluetoothButton(ButtonEntity):
    """Button to add the currently connected Bluetooth device as an input option."""

    _attr_has_entity_name = True
    _attr_name = "Add current Bluetooth device"
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_add_bt_device"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN,
            "add_bluetooth_device",
            {"entry_id": self.entry.entry_id},
            blocking=True,
        )
