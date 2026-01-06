"""DataUpdateCoordinator for JBL 4305P."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import JBL4305PClient, JBL4305PConnectionError
from .const import LOGGER


class JBL4305PDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching JBL 4305P data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: JBL4305PClient,
        update_interval: int,
    ) -> None:
        """Initialize."""
        self.client = client
        self._last_bt_device_path: str | None = None
        super().__init__(
            hass,
            LOGGER,
            name="JBL 4305P",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            player_state = await self.client.get_player_state()
            current_input = await self.client.get_current_input()
            system_info = await self.client.get_system_info()

            # Try to get versions/network but don't fail setup if it errors
            versions_net = {}
            try:
                versions_net = await self.client.get_versions_and_network()
            except Exception as err:
                LOGGER.debug("Failed to fetch versions/network info: %s", err)

            # Track last seen Bluetooth device path
            if player_state:
                media_roles = player_state.get("mediaRoles", {})
                media_data = media_roles.get("mediaData", {})
                meta = media_data.get("metaData", {})
                if meta.get("serviceID") == "bluetooth":
                    val = media_roles.get("value", {})
                    path = val.get("string_")
                    if path:
                        self._last_bt_device_path = path

            return {
                "player_state": player_state or {},
                "current_input": current_input,
                "state": player_state.get("state") if player_state else "unknown",
                "system": system_info,
                "versions": versions_net,
                "last_bt_device_path": self._last_bt_device_path,
            }
        except JBL4305PConnectionError as err:
            # Mark update failed but do not crash; this will make entities unavailable until next success
            raise UpdateFailed(f"Error communicating with API: {err}") from err
