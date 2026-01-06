"""Sensors for JBL 4305P."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ENTITY_CATEGORY_DIAGNOSTIC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JBL4305PDataUpdateCoordinator


SENSORS = [
    ("device_version", "Device Version", None),
    ("airplay_version", "AirPlay Version", None),
    ("cast_version", "Cast Version", None),
    ("ip_cidr", "IP (CIDR)", None),
    ("gateway", "Gateway", None),
    ("dns", "DNS", None),
    ("mac", "MAC Address", None),
    ("serial", "Serial Number", None),
    ("uptime", "Device Uptime", SensorDeviceClass.DURATION),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JBL4305PDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities: list[JBL4305PSensor] = []

    for key, name, device_class in SENSORS:
        entities.append(JBL4305PSensor(coordinator, entry, key, name, device_class))

    async_add_entities(entities)


class JBL4305PSensor(CoordinatorEntity[JBL4305PDataUpdateCoordinator], SensorEntity):
    """Generic sensor for system/version/network info."""

    _attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC

    def __init__(
        self,
        coordinator: JBL4305PDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        device_class: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        if device_class:
            self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get("name", "JBL 4305P"),
            "manufacturer": "JBL",
            "model": "4305P",
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        # Prefer NSDK system info values
        sys_info = data.get("system", {})
        if self._key in sys_info:
            return sys_info.get(self._key)
        # Fallback to parsed versions/network info
        vers = data.get("versions", {})
        return vers.get(self._key)
