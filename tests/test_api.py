"""Tests for JBL 4305P API client."""

import os
import sys

import pytest

# Add custom_components to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components"))

from jbl_4305p.api import JBL4305PClient


@pytest.mark.asyncio
async def test_get_device_name_typed_value(mock_aiohttp_session):
    """Test parsing NSDK typed string response."""
    session, response = mock_aiohttp_session
    response.status = 200
    response.json.return_value = [{"string_": "Lounge Speakers", "type": "string_"}]

    client = JBL4305PClient("192.168.1.75", session)
    name = await client.get_device_name()

    assert name == "Lounge Speakers"


@pytest.mark.asyncio
async def test_get_device_name_plain_string(mock_aiohttp_session):
    """Test parsing plain string response (fallback)."""
    session, response = mock_aiohttp_session
    response.status = 200
    response.json.return_value = ["Lounge Speakers"]

    client = JBL4305PClient("192.168.1.75", session)
    name = await client.get_device_name()

    assert name == "Lounge Speakers"


@pytest.mark.asyncio
async def test_get_device_name_empty(mock_aiohttp_session):
    """Test handling empty response."""
    session, response = mock_aiohttp_session
    response.status = 200
    response.json.return_value = []

    client = JBL4305PClient("192.168.1.75", session)
    name = await client.get_device_name()

    assert name is None


@pytest.mark.asyncio
async def test_discover_bluetooth_devices(mock_aiohttp_session):
    """Test Bluetooth device discovery from player state."""
    session, response = mock_aiohttp_session
    response.status = 200
    # Mock response for player:player/data - returns list with player state object
    response.json.return_value = [
        {
            "state": "playing",
            "mediaRoles": {
                "value": {"string_": "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3", "type": "string_"},
                "title": "[TV] Lounge TV",
                "mediaData": {"metaData": {"serviceID": "bluetooth"}},
            },
        }
    ]

    client = JBL4305PClient("192.168.1.75", session)
    devices = await client.discover_bluetooth_devices()

    assert len(devices) == 1
    device_path = "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3"
    assert device_path in devices
    assert devices[device_path]["name"] == "[TV] Lounge TV"
    assert devices[device_path]["mac"] == "64:e7:d8:6d:ad:c3"


@pytest.mark.asyncio
async def test_get_current_input_googlecast(mock_aiohttp_session):
    """Test getting current input for Google Cast."""
    session, response = mock_aiohttp_session
    response.status = 200
    # Mock response for player:player/data
    response.json.return_value = [
        {
            "state": "playing",
            "mediaRoles": {"mediaData": {"metaData": {"serviceID": "googlecast"}}},
        }
    ]

    client = JBL4305PClient("192.168.1.75", session)
    current = await client.get_current_input()

    assert current == "googlecast"


@pytest.mark.asyncio
async def test_get_current_input_bluetooth_with_device(mock_aiohttp_session):
    """Test getting current input for Bluetooth with device path."""
    session, response = mock_aiohttp_session
    response.status = 200
    # Mock response for player:player/data
    response.json.return_value = [
        {
            "state": "playing",
            "mediaRoles": {
                "value": {"string_": "/org/bluez/hci0/dev_64_E7_D8_6D_AD_C3"},
                "mediaData": {"metaData": {"serviceID": "bluetooth"}},
            },
        }
    ]

    client = JBL4305PClient("192.168.1.75", session)
    current = await client.get_current_input()

    assert current == "bluetooth_64_e7_d8_6d_ad_c3"
