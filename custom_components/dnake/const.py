from homeassistant.const import Platform
from typing import Final

DOMAIN: Final = "dnake"

MANUFACTURER: Final = "dnake"
SW_VERSION: Final = "1.1.0"

DEVICE_ID: Final = "device_id"

SIP_PORT: Final = 5060
SENSOR_LAST_EVENT: Final = 'last_event'

# MQTT Server Configuration
CONF_MQTT_SUPPORT: Final = "mqtt_support"
CONF_MQTT_BROKER: Final = "mqtt_broker"
CONF_MQTT_PORT= "mqtt_port"
CONF_MQTT_KEEPALIVE: Final = "mqtt_keepalive"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"
CONF_MQTT_TOPIC: Final = 'mqtt_topic'

DEFAULT_MQTT_PORT: Final = 1883
DEFAULT_MQTT_KEEPALIVE: Final = 120
DEFAULT_MQTT_TOPIC: Final = 'homeassistant/dnake'

# Dnake Configuration
CONF_BUILD: Final = "build"
CONF_UNIT: Final = 'unit'
CONF_ROOM: Final = 'room'
CONF_IP_ADDRESS: Final = 'ip_address'
CONF_PORT: Final = 'port'
CONF_FAMILY: Final = 'family'
CONF_ELEV_ID: Final = "elev_id"

DEFAULT_PORT: Final = 5060
DEFAULT_FAMILY: Final = 1
DEFAULT_ELEV_ID: Final = 0

CONF_OPENWRT_ADDREDD: Final = "openwrt_address"
CONF_RING_PORT: Final = 'ring_port'
DEFAULT_RING_PORT: Final = 30884

CONF_STATIONS: Final = 'stations'
CONF_LIVE_SUPPORT: Final = 'live_supprt'

from pathlib import Path
STATION_FILENAME: Final = Path(__file__).parent / 'stations.json'

STATIONS: Final = 'stations'
STATION_LIST: Final = 'station_list'
STATION_SELECTED: Final = 'station_selected'

PLATFORMS: Final = [
    Platform.BUTTON,
    Platform.SELECT,
    Platform.CAMERA,
    Platform.SENSOR
]
