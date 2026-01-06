# JBL 4305P Home Assistant Integration

[![CI](https://github.com/mcinnes01/jbl-4305p-hass/actions/workflows/ci.yml/badge.svg)](https://github.com/mcinnes01/jbl-4305p-hass/actions/workflows/ci.yml) [![Release](https://img.shields.io/github/v/release/mcinnes01/jbl-4305p-hass)](https://github.com/mcinnes01/jbl-4305p-hass/releases)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Custom Home Assistant integration for controlling JBL 4305P powered speakers via their local NSDK API.

## Features

- 🎵 **Input Switching**: Select between Google Cast, Bluetooth, AirPlay, Spotify Connect, and other available inputs
- 🔍 **Auto-Discovery**: Automatically discovers available inputs and paired Bluetooth devices
- 🔄 **Real-time Updates**: Monitors current input and playback state
- ⚙️ **Configurable**: Set custom update intervals and log levels
- 📱 **Multiple Speakers**: Support for multiple JBL 4305P speakers on your network

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right and select "Custom repositories"
4. Add `https://github.com/mcinnes01/jbl-4305p-hass` and select "Integration" as the category
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/jbl_4305p` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Adding a Speaker

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "JBL 4305P"
4. Enter your speaker's IP address (e.g., `192.168.1.75`)
5. Optionally set:
   - Speaker name (or leave blank to use the name from the speaker)
   - Update interval (default: 30 seconds)
   - Log level (default: info)
6. Click **Submit**

The integration will automatically discover available inputs including:
- Google Cast (Chromecast built-in)
- Bluetooth devices (currently paired)
- AirPlay
- Spotify Connect
- Tidal Connect
- Roon
- UPnP/DLNA

### Options

After adding the integration, you can configure additional options:

1. Go to **Settings** → **Devices & Services**
2. Find your JBL 4305P speaker
3. Click **Configure**
4. Adjust:
   - **Update Interval**: How often to poll the speaker (10-300 seconds)
   - **Log Level**: Set logging verbosity (debug, info, warning, error)
   - **Rediscover Inputs**: Enable this to rescan for new Bluetooth devices or inputs

## Usage

### Input Selection

Once configured, you'll have a `select.jbl_4305p_input_source` entity (or similar, based on your speaker name).

**In the UI:**
- Go to the device page and use the dropdown to select an input

**With Automations:**
```yaml
service: select.select_option
target:
  entity_id: select.jbl_4305p_input_source
data:
  option: "Google Cast"
```

**Available Options:**
- `Google Cast` - Chromecast built-in
- `Bluetooth - [Device Name]` - Specific Bluetooth device (e.g., "Bluetooth - Lounge TV")
- `AirPlay` - Apple AirPlay
- `Spotify Connect` - Spotify Connect
- And others based on what's available on your speaker

### Example Automation

Switch to Bluetooth when TV turns on:
```yaml
automation:
  - alias: "Switch speakers to TV audio"
    trigger:
      - platform: state
        entity_id: media_player.living_room_tv
        to: "on"
    action:
      - service: select.select_option
        target:
          entity_id: select.jbl_4305p_input_source
        data:
          option: "Bluetooth - Lounge TV"
```

## Bluetooth Device Discovery

The integration automatically discovers Bluetooth devices that are:
1. Currently paired with the speaker
2. Actively playing or recently played

**To add new Bluetooth devices:**
1. Pair the device with your speaker using the speaker's Bluetooth button
2. Start playing audio from the device
3. In Home Assistant, go to the integration options and enable "Rediscover Inputs"
4. Save - the new device will be added to the input list

Each Bluetooth device gets its own input option with its friendly name (e.g., "Bluetooth - iPhone", "Bluetooth - Samsung TV").

## Technical Details

### NSDK API

This integration uses the speaker's NSDK (Network SDK) HTTP API:
- **Endpoint**: `http://[SPEAKER_IP]/api/getData` and `/api/setData`
- **Protocol**: HTTP GET with query parameters
- **Authentication**: None (local network only)

### Supported Inputs

The integration probes for these service types:
- `googlecast` - Google Cast / Chromecast
- `bluetooth` - Bluetooth devices (with device-specific paths)
- `airplay` - Apple AirPlay
- `spotify` - Spotify Connect
- `roon` - Roon Ready
- `tidalConnect` - Tidal Connect
- `upnpRenderer` - UPnP/DLNA

Only inputs that are available on your specific speaker model will appear in the dropdown.

## Troubleshooting

### Cannot Connect Error

- Verify the IP address is correct
- Ensure the speaker is powered on and connected to the network
- Check that your Home Assistant instance can reach the speaker (same network/VLAN)
- Try accessing `http://[SPEAKER_IP]/api/getData?path=settings:/deviceName&roles=value` in a browser

### Bluetooth Device Not Showing

- Ensure the device is paired with the speaker (use the speaker's Bluetooth button)
- Play audio from the Bluetooth device first
- Use the "Rediscover Inputs" option in the integration settings
- Check the Home Assistant logs for discovery errors

### Input Switch Not Working

- Check the integration logs (set log level to "debug" in options)
- For Bluetooth, ensure the device is powered on and in range
- Some inputs may require the source device to be actively available

### Logs

To enable detailed logging, add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.jbl_4305p: debug
```

## Development

### File Structure
```
custom_components/jbl_4305p/
├── __init__.py           # Integration setup
├── api.py                # NSDK API client
├── config_flow.py        # Configuration UI
├── const.py              # Constants
├── coordinator.py        # Data update coordinator
├── manifest.json         # Integration metadata
├── select.py             # Input select entity
├── strings.json          # UI strings
└── translations/
    └── en.json           # English translations
```

### API Methods

Key methods in `api.py`:
- `discover_available_inputs()` - Scans for all available inputs
- `discover_bluetooth_devices()` - Finds paired Bluetooth devices
- `switch_input(service_id, device_path)` - Changes input
- `get_current_input()` - Gets active input
- `get_player_state()` - Gets current playback state

## License

MIT License - see LICENSE file for details

## Support

For issues or feature requests, please [open an issue on GitHub](https://github.com/mcinnes01/jbl-4305p-hass/issues).

## Credits

Reverse-engineered from JBL 4305P speaker logs and web interface.
