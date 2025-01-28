"""Button platform for PetKit integration."""
from __future__ import annotations
from typing import Any

from homeassistant.components.button import ButtonEntity

from .const import (
    DOMAIN, 
    MANUFACTURER, 
    SW_VERSION, 

    SIP_PORT, 
    STATIONS, 
    STATION_SELECTED, 
    DEVICE_ID
)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    sensors = [
        DnakeButton(hass=hass, client=hass.data[DOMAIN][entry.entry_id], device_id = hass.data[DOMAIN][DEVICE_ID], translation_key = 'unlock'),
        DnakeButton(hass=hass, client=hass.data[DOMAIN][entry.entry_id], device_id = hass.data[DOMAIN][DEVICE_ID], translation_key = 'elev_permit'),
        DnakeButton(hass=hass, client=hass.data[DOMAIN][entry.entry_id], device_id = hass.data[DOMAIN][DEVICE_ID], translation_key = 'elev_up'),
        DnakeButton(hass=hass, client=hass.data[DOMAIN][entry.entry_id], device_id = hass.data[DOMAIN][DEVICE_ID], translation_key = 'elev_down'),
    ]
    async_add_entities(sensors)

class DnakeButton(ButtonEntity):
    def __init__(self, hass, client, device_id, translation_key):
        self._hass = hass
        self._client = client
        self._device_id = device_id
        self._translation_key = translation_key

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_id,
            "manufacturer": MANUFACTURER,
            "sw_version": SW_VERSION
        }

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._device_id}_{self._translation_key}"

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def translation_key(self) -> str:
        return self._translation_key

    @property
    def available(self) -> bool:
        return True
        
    async def async_press(self) -> None:
        try:
            id = self._hass.data[DOMAIN][STATION_SELECTED]
            ip = self._hass.data[DOMAIN][STATIONS][id]
            port = SIP_PORT
            if self._translation_key == 'unlock':
                await self._client.unlock(id, ip, port)
            elif self._translation_key == 'elev_permit':
                await self._client.permit(id, ip, port)
            elif self._translation_key == 'elev_up':
                await self._client.appoint(id, ip, port, 1)
            elif self._translation_key == 'elev_down':
                await self._client.appoint(id, ip, port, 2)
        except Exception as e:
            raise Exception(e)
