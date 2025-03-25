from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template
import yarl
from typing import Final

from .const import (
    DOMAIN, 
    MANUFACTURER, 
    SW_VERSION, 

    DEVICE_ID, 
    STATIONS, 
    CONF_LIVE_SUPPORT,
)

import logging
_LOGGER = logging.getLogger(__name__)

RTSP_USERNAME: Final = "admin"
RTSP_PASSWORD: Final = "123456"

async def async_setup_entry(hass, entry, async_add_entities):
    sensors = []
    if entry.data[CONF_LIVE_SUPPORT]:
        for key, val in hass.data[DOMAIN][STATIONS].items():
            sensors.append(RTSPCamera(hass=hass, device_id=hass.data[DOMAIN][DEVICE_ID], name=f'{DOMAIN}_{key}', address=val))
    async_add_entities(sensors)

class RTSPCamera(Camera):
    def __init__(self, hass, device_id, name, address):
        super().__init__()
        self._hass = hass
        self._name = name
        self._device_id = device_id
        self._attr_current_option = None
        self._stream_source = Template(f"rtsp://{address}:8554/ch01", self._hass)
        self._attr_frame_interval = 1 / 15
        self._attr_supported_features = CameraEntityFeature.STREAM

    @property
    def use_stream_for_stills(self) -> bool:
        """Whether or not to use stream to generate stills."""
        return True

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._device_id}_{self._name}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_id,
            "manufacturer": MANUFACTURER,
            "sw_version": SW_VERSION
        }

    @property
    def use_stream_for_stills(self):
        """Whether or not to use stream to generate stills."""
        return True

    async def async_camera_image(self, width=None, height=None):
        """Return a still image from the camera."""
        return None

    @property
    def name(self) -> str:
        """Return the name of this device."""
        return self._name

    @property
    def is_streaming(self):
        """Return true if the camera is streaming."""
        return True

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        try:
            stream_url = self._stream_source.async_render(parse_result=False)
            url = yarl.URL(stream_url)
            url = url.with_user(RTSP_USERNAME).with_password(RTSP_PASSWORD)
            return str(url)
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._stream_source, err)
            return None