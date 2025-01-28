from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from asyncio import create_task
import json
from datetime import datetime
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer

from .client import Client
from .const import (
    DOMAIN, 
    PLATFORMS, 
    DEVICE_ID, 
    SIP_PORT,
    CONF_RING_PORT,

    CONF_MQTT_TOPIC,

    STATIONS, 
    STATION_LIST,

    SENSOR_LAST_EVENT, 
    STATION_FILENAME, 
)
from .utils import save_json, load_json

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug(f'entry.data: {entry.data}')

    hass.data.setdefault(DOMAIN, {})

    # Initialize Dnake Client
    client = Client(hass, entry.data)
    await client.initialize()

    # Initialize http server
    server_thread = threading.Thread(
        target=ring_service, 
        kwargs={'hass': hass, 'entry_id': entry.entry_id, 'mqtt_topic': entry.data[CONF_MQTT_TOPIC], 'port': entry.data[CONF_RING_PORT]}
    )
    server_thread.start()

    hass.data[DOMAIN][entry.entry_id] = client
    hass.data[DOMAIN][DEVICE_ID] = client.src_id
    hass.data[DOMAIN][STATIONS] = await load_json(STATION_FILENAME)
    hass.data[DOMAIN][STATION_LIST] = list(hass.data[DOMAIN][STATIONS].keys())

    async def appoint(call):
        """Handle the service call."""
        dst_id = call.data.get('dst_id')
        dst_ip = call.data.get('dst_ip')
        direct = call.data.get('direct')
        _LOGGER.debug(f'appoint request received as {call.data}.')
        try:
            await client.appoint(dst_id=dst_id, dst_ip=dst_ip, dst_port=SIP_PORT, direct=direct)
            _LOGGER.debug(f'appoint request executed.')
            hass.bus.fire('dnake.appoint', {'status': 'success'})
        except Exception as e:
            _LOGGER.debug(f'appoint request failed: {e}.')
            hass.bus.fire('dnake.appoint', {'status': 'error', 'message': str(e)})
    hass.services.async_register(DOMAIN, 'appoint', appoint)

    async def unlock(call):
        """Handle the service call."""
        dst_id = call.data.get('dst_id')
        dst_ip = call.data.get('dst_ip')
        _LOGGER.debug(f'unlock request received as {call.data}.')
        try:
            await client.unlock(dst_id=dst_id, dst_ip=dst_ip, dst_port=SIP_PORT)
            _LOGGER.debug(f'unlock request executed.')
            hass.bus.fire('dnake.unlock', {'status': 'success'})
        except Exception as e:
            _LOGGER.debug(f'unlock request failed: {e}.')
            hass.bus.fire('dnake.unlock', {'status': 'error', 'message': str(e)})
    hass.services.async_register(DOMAIN, 'unlock', unlock)

    async def permit(call):
        """Handle the service call."""
        dst_id = call.data.get('dst_id')
        dst_ip = call.data.get('dst_ip')
        _LOGGER.debug(f'permit request received as {call.data}.')
        try:
            await client.permit(dst_id=dst_id, dst_ip=dst_ip, dst_port=SIP_PORT)
            _LOGGER.debug(f'permit request executed.')
            hass.bus.fire('dnake.permit', {'status': 'success'})
        except Exception as e:
            _LOGGER.debug(f'permit request failed: {e}.')
            hass.bus.fire('dnake.permit', {'status': 'error', 'message': str(e)})
    hass.services.async_register(DOMAIN, 'permit', permit)

    async def execute(call):
        """Handle the service call."""
        json_data = call.data.get('json_data')
        _LOGGER.debug(f'execute request received as {call.data}.')
        try:
            await client.execute(json_data)
            _LOGGER.debug(f'execute request executed.')
            hass.bus.fire('dnake.execute', {'status': 'success'})
        except Exception as e:
            _LOGGER.debug(f'execute request failed: {e}.')
            hass.bus.fire('dnake.execute', {'status': 'error', 'message': str(e)})
    hass.services.async_register(DOMAIN, 'execute', execute)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, hass, entry_id, mqtt_topic, *args, **kwargs):
        self._hass = hass
        self._entry_id = entry_id
        self._mqtt_topic = mqtt_topic
        super().__init__(*args, **kwargs)

    def _set_headers(self):
        self.send_response(200)
        self.end_headers()

    def handle_post(self, payloads):
        if '@' in payloads.get('from', ''):
            # update saved clients
            src_id, src_ip = payloads['from'].split('@')
            src_ip = src_ip.split(':')[0]
            dst_id, dst_ip = payloads['to'].split('@')
            dst_ip = dst_ip.split(':')[0]
            if src_id not in self._hass.data[DOMAIN][STATION_LIST]:
                self._hass.data[DOMAIN][STATION_LIST].append(src_id)
                self._hass.data[DOMAIN][STATIONS][src_id] = src_ip
                self._hass.loop.call_soon_threadsafe(create_task, save_json(self._hass.data[DOMAIN][STATIONS], STATION_FILENAME))

            state_attributes = {
                'event': 'ring',
                'src_id': src_id,
                'src_ip': src_ip,
                'dst_id': dst_id,
                'dst_ip': dst_ip,
                'time': datetime.now().isoformat()
            }
            # update sensor
            self._hass.loop.call_soon_threadsafe(
                async_dispatcher_send,
                self._hass,
                f"{DOMAIN}_{self._hass.data[DOMAIN][DEVICE_ID]}_{SENSOR_LAST_EVENT}",
                state_attributes
            )

            # mqtt publish
            mqtt_client = self._hass.data[DOMAIN][self._entry_id].client
            if mqtt_client:
                mqtt_client.publish(self._mqtt_topic, json.dumps(state_attributes, ensure_ascii=False))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            payloads = json.loads(post_data.decode('utf-8'))
            _LOGGER.debug(f"Received data: {payloads}")

            self.handle_post(payloads)

            self._set_headers()

        except UnicodeDecodeError as e:
            _LOGGER.debug(f"UnicodeDecodeError: {e}")
            self.send_response(400)
            self.end_headers()
        except Exception as e:
            _LOGGER.debug(f"Exception: {e}")

def ring_service(server_class=HTTPServer, handler_class=RequestHandler, hass=None, entry_id=None, mqtt_topic=None, port=30884):
    server_address = ('', port)
    handler = partial(handler_class, hass, entry_id, mqtt_topic)
    httpd = server_class(server_address, handler)
    _LOGGER.debug(f"Http server running on port {port}")
    httpd.serve_forever()
