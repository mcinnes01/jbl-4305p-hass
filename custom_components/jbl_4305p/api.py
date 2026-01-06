"""API client for JBL 4305P speakers."""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import aiohttp
import re

from .const import LOGGER


class JBL4305PApiError(Exception):
    """Base exception for API errors."""


class JBL4305PConnectionError(JBL4305PApiError):
    """Connection error."""


class JBL4305PClient:
    """Client for JBL 4305P NSDK API."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the client."""
        self.host = host
        self.session = session
        self.base_url = f"http://{host}"

    async def nsdk_get_data(
        self, path: str, roles: str = "value"
    ) -> list[dict[str, Any]]:
        """Get data from NSDK API."""
        url = f"{self.base_url}/api/getData"
        params = {
            "path": path,
            "roles": roles,
            "_nocache": str(int(time.time() * 1000)),
        }

        try:
            async with self.session.get(url, params=params, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                if isinstance(data, dict) and "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    LOGGER.debug("NSDK API error for path %s: %s", path, error_msg)
                    return []
                
                return data if isinstance(data, list) else []
        except aiohttp.ClientError as err:
            raise JBL4305PConnectionError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise JBL4305PConnectionError("Request timeout") from err

    async def nsdk_set_data(
        self, path: str, value: Any, role: str = "activate"
    ) -> bool:
        """Set data via NSDK API."""
        url = f"{self.base_url}/api/setData"
        params = {
            "path": path,
            "role": role,
            "value": json.dumps(value),
            "_nocache": str(int(time.time() * 1000)),
        }

        try:
            async with self.session.get(url, params=params, timeout=10) as resp:
                resp.raise_for_status()
                return True
        except aiohttp.ClientError as err:
            LOGGER.error("Failed to set data: %s", err)
            return False

    async def get_device_name(self) -> str | None:
        """Get device name from NSDK settings, handling typed values."""
        data = await self.nsdk_get_data("settings:/deviceName")
        if not data:
            return None
        value = data[0]
        # Handle either a raw string or typed object {"string_": "name"}
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and value.get("type") == "string_":
            return value.get("string_")
        return None

    async def set_device_name(self, name: str) -> bool:
        """Set device name via NSDK settings."""
        payload = {"string_": name, "type": "string_"}
        return await self.nsdk_set_data("settings:/deviceName", payload, role="value")

    async def get_player_state(self) -> dict[str, Any] | None:
        """Get current player state."""
        data = await self.nsdk_get_data("player:player/data")
        return data[0] if data else None

    async def get_system_info(self) -> dict[str, Any]:
        """Get system info from NSDK settings if available."""
        info: dict[str, Any] = {}
        # Known settings
        for path, key in [
            ("settings:/system/primaryMacAddress", "mac"),
            ("settings:/system/serialNumber", "serial"),
            ("settings:/system/deviceUptime", "uptime"),
            ("settings:/googlecast/castVersion", "cast_version"),
        ]:
            try:
                val = await self.nsdk_get_data(path)
                if val:
                    v = val[0]
                    if isinstance(v, dict) and "type" in v:
                        info[key] = v.get(v.get("type"))
                    else:
                        info[key] = v
            except Exception:  # best effort
                pass
        return info

    async def get_versions_and_network(self) -> dict[str, Any]:
        """Parse index.fcgi for device version and network info as fallback."""
        out: dict[str, Any] = {}
        try:
            async with self.session.get(f"{self.base_url}/index.fcgi", timeout=10) as resp:
                text = await resp.text()
        except Exception as err:  # noqa: BLE001
            LOGGER.debug("Failed to fetch index.fcgi: %s", err)
            return out

        # Regex extraction
        m = re.search(r"Device version:\s*([^<\n]+)", text)
        if m:
            out["device_version"] = m.group(1).strip()
        m = re.search(r"AirPlay version:\s*([^<\n]+)", text)
        if m:
            out["airplay_version"] = m.group(1).strip()
        m = re.search(r"IP:\s*([\d\.]+/\d+)", text)
        if m:
            out["ip_cidr"] = m.group(1).strip()
        m = re.search(r"Gateway:\s*([\d\.]+)", text)
        if m:
            out["gateway"] = m.group(1).strip()
        m = re.search(r"DNS:\s*([^<\n]+)", text)
        if m:
            out["dns"] = ", ".join([d.strip() for d in m.group(1).split(",")])
        return out

    async def discover_bluetooth_devices(self) -> dict[str, dict[str, Any]]:
        """Discover paired Bluetooth devices from player state and logs."""
        devices = {}
        
        # Get current player state to check for active Bluetooth device
        player_state = await self.get_player_state()
        
        if player_state and player_state.get("state") != "stopped":
            media_roles = player_state.get("mediaRoles", {})
            media_data = media_roles.get("mediaData", {})
            meta_data = media_data.get("metaData", {})
            
            # Check if current input is Bluetooth
            if meta_data.get("serviceID") == "bluetooth":
                # Extract device path from value
                value = media_roles.get("value", {})
                device_path = value.get("string_")
                title = media_roles.get("title", "Unknown Device")
                
                if device_path:
                    # Extract MAC from path: /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX
                    parts = device_path.split("/")
                    if len(parts) >= 5 and parts[-2].startswith("dev_"):
                        mac = parts[-2].replace("dev_", "").replace("_", ":")
                        devices[device_path] = {
                            "name": title,
                            "mac": mac,
                            "path": device_path,
                        }
        
        return devices

    async def discover_available_inputs(self) -> dict[str, dict[str, Any]]:
        """Discover all available inputs on the speaker."""
        inputs = {}
        
        # Add Google Cast (always available if speaker supports it)
        inputs["googlecast"] = {
            "service_id": "googlecast",
            "name": "Google Cast",
            "type": "googlecast",
        }
        
        # Check for Bluetooth devices
        bt_devices = await self.discover_bluetooth_devices()
        for device_path, device_info in bt_devices.items():
            input_id = f"bluetooth_{device_info['mac'].replace(':', '_').lower()}"
            inputs[input_id] = {
                "service_id": "bluetooth",
                "name": f"Bluetooth - {device_info['name']}",
                "type": "bluetooth",
                "device_path": device_path,
                "device_name": device_info["name"],
            }
        
        # Add generic Bluetooth option if no specific devices found
        if not bt_devices:
            inputs["bluetooth"] = {
                "service_id": "bluetooth",
                "name": "Bluetooth",
                "type": "bluetooth",
            }
        
        # Check for other services by probing paths
        # Note: These may return errors if not available, which is expected
        other_services = {
            "airplay": "AirPlay",
            "spotify": "Spotify Connect",
            "roon": "Roon",
            "tidalConnect": "Tidal Connect",
            "upnpRenderer": "UPnP/DLNA",
        }
        
        for service_id, service_name in other_services.items():
            # Try to read service config to see if it exists
            data = await self.nsdk_get_data(f"settings:/{service_id}")
            if data:  # Service exists
                inputs[service_id] = {
                    "service_id": service_id,
                    "name": service_name,
                    "type": service_id,
                }
        
        return inputs

    async def switch_input(
        self, service_id: str, device_path: str | None = None
    ) -> bool:
        """Switch to specified input."""
        if service_id == "googlecast":
            payload = {
                "control": "play",
                "mediaRoles": {
                    "mediaData": {
                        "metaData": {
                            "live": True,
                            "serviceID": "googlecast",
                        }
                    },
                    "type": "audio",
                    "audioType": "audioBroadcast",
                    "title": "Chromecast built-in",
                    "icon": "skin:iconGooglecast",
                    "doNotTrack": True,
                    "description": "Chromecast built-in",
                },
            }
        elif service_id == "bluetooth":
            payload = {
                "control": "play",
                "mediaRoles": {
                    "type": "audio",
                    "audioType": "audioBroadcast",
                    "mediaData": {
                        "metaData": {
                            "serviceID": "bluetooth",
                            "playLogicPath": "bluetooth:playlogic",
                        }
                    },
                    "doNotTrack": True,
                },
            }
            
            # Add device path if provided
            if device_path:
                payload["mediaRoles"]["value"] = {
                    "string_": device_path,
                    "type": "string_",
                }
        else:
            # Generic service activation
            payload = {
                "control": "play",
                "mediaRoles": {
                    "type": "audio",
                    "audioType": "audioBroadcast",
                    "mediaData": {
                        "metaData": {
                            "serviceID": service_id,
                        }
                    },
                },
            }

        return await self.nsdk_set_data("player:player/control", payload)

    async def get_current_input(self) -> str | None:
        """Get current active input service ID."""
        player_state = await self.get_player_state()
        
        if not player_state or player_state.get("state") == "stopped":
            return None
        
        media_roles = player_state.get("mediaRoles", {})
        media_data = media_roles.get("mediaData", {})
        meta_data = media_data.get("metaData", {})
        service_id = meta_data.get("serviceID")
        
        # For Bluetooth, include device path in ID
        if service_id == "bluetooth":
            value = media_roles.get("value", {})
            device_path = value.get("string_")
            if device_path:
                parts = device_path.split("/")
                if len(parts) >= 5 and parts[-2].startswith("dev_"):
                    mac = parts[-2].replace("dev_", "").replace("_", ":").lower()
                    return f"bluetooth_{mac.replace(':', '_')}"
        
        return service_id
