from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN, 
    MANUFACTURER, 
    SW_VERSION, 

    DEVICE_ID, 

    STATION_LIST, 
    STATION_SELECTED, 
)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    sensors = [
        DnakeSelect(hass=hass, device_id = hass.data[DOMAIN][DEVICE_ID], translation_key = 'contact_id', options=hass.data[DOMAIN][STATION_LIST]),
    ]
    async_add_entities(sensors)

class DnakeSelect(SelectEntity, RestoreEntity):
    def __init__(self, hass, device_id, translation_key, options):
        self._hass = hass
        self._device_id = device_id
        self._name = device_id
        self._translation_key = translation_key
        self._attr_options = options
        self._attr_current_option = None

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._device_id}_{self._translation_key}"

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_id,
            "manufacturer": MANUFACTURER,
            "sw_version": SW_VERSION
        }

    @property
    def translation_key(self) -> str:
        return self._translation_key

    def update_options(self):
        self._attr_options = self._hass.data[DOMAIN][STATION_LIST]
        self.async_write_ha_state()

    async def async_select_option(self, option):
        self._attr_current_option = option
        self._hass.data[DOMAIN][STATION_SELECTED] = option
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        # Restore state
        old_state = await self.async_get_last_state()
        if old_state and old_state.state in self._attr_options:
            self._attr_current_option = old_state.state
        elif self._attr_options:
            self._attr_current_option = self._attr_options[0]
        self._hass.data[DOMAIN][STATION_SELECTED] =  self._attr_current_option

 # type: ignore