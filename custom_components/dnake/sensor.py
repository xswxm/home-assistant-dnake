from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import STATE_UNKNOWN
from .const import (
    DOMAIN, 
    MANUFACTURER, 
    SW_VERSION, 

    DEVICE_ID,
    SENSOR_LAST_EVENT, 
)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    sensors = [
        DnakeSensor(device_id=hass.data[DOMAIN][DEVICE_ID], sensor_id=SENSOR_LAST_EVENT, translation_key='last_event'),
    ]
    async_add_entities(sensors)

class DnakeSensor(SensorEntity, RestoreEntity):
    def __init__(self, device_id, sensor_id, translation_key):
        self._device_id = device_id
        self._sensor_id = sensor_id
        self._state = None
        self._translation_key = translation_key
        self._state = STATE_UNKNOWN
        self._extra_state_attributes = None

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._device_id}_{self._sensor_id}"

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
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""

        return True

    @property
    def translation_key(self) -> str:
        return self._translation_key

    @property
    def icon(self) -> str:
        """Set icon."""

        return 'mdi:calendar'

    @property
    def entity_category(self) -> EntityCategory:
        """Set category to diagnostic."""
        return EntityCategory.DIAGNOSTIC

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_added_to_hass(self):
        """Restore state when the entity is added to Home Assistant."""
        # Restore state
        old_state = await self.async_get_last_state()
        if old_state:
            self._state = old_state.state
            self._extra_state_attributes = old_state.attributes

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.unique_id, self.update_state
            )
        )

    def update_state(self, state_attributes):
        """Update the sensor state and attributes."""
        self._state = state_attributes['event']
        self._extra_state_attributes = state_attributes
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
