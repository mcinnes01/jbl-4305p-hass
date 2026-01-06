"""JBL 4305P integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JBL4305PClient
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import JBL4305PDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SELECT, Platform.SENSOR]


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
