"""Constants for the JBL 4305P integration."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "jbl_4305p"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOG_LEVEL = "log_level"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_LOG_LEVEL = "info"

# NSDK API paths
PATH_PLAYER_CONTROL = "player:player/control"
PATH_PLAYER_DATA = "player:player/data"
PATH_DEVICE_NAME = "settings:/deviceName"
PATH_BLUETOOTH_SETTINGS = "settings:/bluetooth"

# Known service IDs
SERVICE_GOOGLECAST = "googlecast"
SERVICE_BLUETOOTH = "bluetooth"
SERVICE_AIRPLAY = "airplay"
SERVICE_SPOTIFY = "spotify"
SERVICE_ROON = "roon"
SERVICE_TIDAL = "tidalConnect"
SERVICE_UPNP = "upnpRenderer"

# Input types
INPUT_TYPES = {
    SERVICE_GOOGLECAST: "Google Cast",
    SERVICE_BLUETOOTH: "Bluetooth",
    SERVICE_AIRPLAY: "AirPlay",
    SERVICE_SPOTIFY: "Spotify Connect",
    SERVICE_ROON: "Roon",
    SERVICE_TIDAL: "Tidal Connect",
    SERVICE_UPNP: "UPnP/DLNA",
}
