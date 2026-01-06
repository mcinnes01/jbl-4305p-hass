"""JBL 4305P integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JBL4305PClient
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import JBL4305PDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SELECT, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JBL 4305P from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = JBL4305PClient(entry.data[CONF_HOST], session)

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = JBL4305PDataUpdateCoordinator(hass, client, scan_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register services once (idempotent)
    async def _async_rediscover_inputs(call):
        """Service to rediscover inputs for a given config entry."""
        target_entry_id = call.data.get("entry_id", entry.entry_id)
        # If a different entry is requested, ignore in this instance
        if target_entry_id != entry.entry_id:
            return
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        inputs = await client.discover_available_inputs()
        # Update options with new inputs and trigger reload via update listener
        new_options = dict(entry.options)
        new_options["available_inputs"] = inputs
        hass.config_entries.async_update_entry(entry, options=new_options)

    if not hass.services.has_service(DOMAIN, "rediscover_inputs"):
        hass.services.async_register(
            DOMAIN,
            "rediscover_inputs",
            _async_rediscover_inputs,
        )

    async def _async_add_bluetooth_device(call):
        """Service to add the currently connected Bluetooth device as an input option.

        Optional fields:
        - entry_id: target config entry (defaults to this entry)
        - name: friendly name to show (defaults to title from player state)
        - device_path: explicit device path to use (defaults to last seen)
        """
        target_entry_id = call.data.get("entry_id", entry.entry_id)
        if target_entry_id != entry.entry_id:
            return

        client = hass.data[DOMAIN][entry.entry_id]["client"]
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        provided_path = call.data.get("device_path")
        provided_name = call.data.get("name")

        device_path = provided_path
        device_name = provided_name

        if not device_path:
            # Prefer last seen Bluetooth device path from coordinator
            device_path = (coordinator.data or {}).get("last_bt_device_path")

        # If still missing, try current player state
        if not device_path:
            state = await client.get_player_state()
            if state:
                mr = state.get("mediaRoles", {})
                md = mr.get("mediaData", {})
                meta = md.get("metaData", {})
                if meta.get("serviceID") == "bluetooth":
                    val = mr.get("value", {})
                    device_path = val.get("string_")
                    device_name = device_name or mr.get("title")

        if not device_path:
            # Nothing to add
            return

        # Derive MAC and input id
        mac_id = None
        parts = device_path.split("/")
        if len(parts) >= 5 and parts[-2].startswith("dev_"):
            mac = parts[-2].replace("dev_", "").lower()
            mac_id = mac.replace(":", "_").replace("_", "_")

        input_id = f"bluetooth_{mac_id}" if mac_id else f"bluetooth_{abs(hash(device_path))}"
        friendly_name = provided_name or device_name or "Bluetooth Device"

        inputs = dict(entry.options.get("available_inputs", {}))
        inputs[input_id] = {
            "service_id": "bluetooth",
            "name": f"Bluetooth - {friendly_name}",
            "type": "bluetooth",
            "device_path": device_path,
            "device_name": friendly_name,
        }

        new_options = dict(entry.options)
        new_options["available_inputs"] = inputs
        hass.config_entries.async_update_entry(entry, options=new_options)

    if not hass.services.has_service(DOMAIN, "add_bluetooth_device"):
        hass.services.async_register(
            DOMAIN,
            "add_bluetooth_device",
            _async_add_bluetooth_device,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
