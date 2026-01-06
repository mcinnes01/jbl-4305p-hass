"""Tests for coordinator data handling."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components"))

from jbl_4305p.coordinator import JBL4305PDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_tracks_last_bluetooth_device():
    """Test that coordinator stores last seen Bluetooth device path."""
    mock_hass = MagicMock()
    mock_client = AsyncMock()
    
    # First update: Bluetooth playing
    mock_client.get_player_state.return_value = {
        "state": "playing",
        "mediaRoles": {
            "value": {"string_": "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3"},
            "mediaData": {"metaData": {"serviceID": "bluetooth"}}
        }
    }
    mock_client.get_current_input.return_value = "bluetooth_64_e7_d8_6d_ad_c3"
    mock_client.get_system_info.return_value = {}
    mock_client.get_versions_and_network.return_value = {}
    
    coordinator = JBL4305PDataUpdateCoordinator(mock_hass, mock_client, 30)
    data = await coordinator._async_update_data()
    
    assert data["last_bt_device_path"] == "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3"
    
    # Second update: Google Cast (Bluetooth path should persist)
    mock_client.get_player_state.return_value = {
        "state": "playing",
        "mediaRoles": {
            "mediaData": {"metaData": {"serviceID": "googlecast"}}
        }
    }
    mock_client.get_current_input.return_value = "googlecast"
    
    data = await coordinator._async_update_data()
    
    # Last Bluetooth path should still be stored
    assert data["last_bt_device_path"] == "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3"
