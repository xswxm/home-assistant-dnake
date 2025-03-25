from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
import json

import time
import asyncio
import paho.mqtt.client as mqtt
from .const import (
    DOMAIN,

    CONF_BUILD,
    CONF_UNIT,
    CONF_ROOM,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_ELEV_ID,
    CONF_FAMILY, 
    DEFAULT_PORT,
    DEFAULT_FAMILY,
    DEFAULT_ELEV_ID, 
    
    CONF_OPENWRT_ADDREDD,
    CONF_RING_PORT,
    CONF_STATIONS,

    CONF_LIVE_SUPPORT,

    SIP_PORT, 
    DEFAULT_RING_PORT,
    

    CONF_MQTT_SUPPORT, 
    CONF_MQTT_BROKER, 
    CONF_MQTT_PORT, 
    CONF_MQTT_KEEPALIVE, 
    CONF_MQTT_USERNAME, 
    CONF_MQTT_PASSWORD, 
    CONF_MQTT_TOPIC, 

    DEFAULT_MQTT_PORT, 
    DEFAULT_MQTT_KEEPALIVE, 
    DEFAULT_MQTT_TOPIC, 

    STATION_FILENAME, 
)
from .utils import save_json, load_json

import logging
_LOGGER = logging.getLogger(__name__)

class DnakeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Example."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""

        self.dnake_build = None
        self.dnake_unit = None
        self.dnake_room = None
        self.dnake_ip_address = ''
        self.dnake_port = DEFAULT_PORT
        self.dnake_family = DEFAULT_FAMILY
        self.dnake_elev_id = DEFAULT_ELEV_ID

        self.openwrt_address = ''
        self.ring_port = None
        self.dnake_stations = {}
        
        self.live_support = False

        self.mqtt_support = False
        self.mqtt_broker = None
        self.mqtt_port = DEFAULT_MQTT_PORT
        self.mqtt_username = None
        self.mqtt_password = None
        self.mqtt_keepalive = DEFAULT_MQTT_KEEPALIVE
        self.mqtt_topic = DEFAULT_MQTT_TOPIC

    async def create_entry(self):
        await save_json(self.dnake_stations, STATION_FILENAME)
        return self.async_create_entry(
                        title=f'{self.dnake_build}{self.dnake_unit:0>2d}{self.dnake_room:0>4d}',
                        data={
                            CONF_BUILD: self.dnake_build,
                            CONF_UNIT: self.dnake_unit,
                            CONF_ROOM: self.dnake_room,
                            CONF_IP_ADDRESS: self.dnake_ip_address,
                            CONF_PORT: self.dnake_port,
                            CONF_FAMILY: self.dnake_family,
                            CONF_ELEV_ID: self.dnake_elev_id,
                            
                            CONF_OPENWRT_ADDREDD: self.openwrt_address,
                            CONF_RING_PORT: self.ring_port,
                            CONF_LIVE_SUPPORT: self.live_support,

                            CONF_MQTT_SUPPORT: self.mqtt_support,
                            CONF_MQTT_BROKER: self.mqtt_broker,
                            CONF_MQTT_PORT: self.mqtt_port,
                            CONF_MQTT_USERNAME: self.mqtt_username,
                            CONF_MQTT_PASSWORD: self.mqtt_password,
                            CONF_MQTT_KEEPALIVE: self.mqtt_keepalive,
                            CONF_MQTT_TOPIC: self.mqtt_topic,
                        },
                    )

    async def async_step_user(self, user_input=None):
        """Handle the first step (dnake input)."""
        if user_input is not None:
            # Save user input for next step
            self.dnake_build = user_input[CONF_BUILD]
            self.dnake_unit = user_input[CONF_UNIT]
            self.dnake_room = user_input[CONF_ROOM]
            self.dnake_ip_address = user_input.get(CONF_IP_ADDRESS, '')
            self.dnake_port = SIP_PORT
            self.dnake_family = user_input.get(CONF_FAMILY, DEFAULT_FAMILY)
            self.dnake_elev_id = user_input.get(CONF_ELEV_ID, DEFAULT_ELEV_ID)

            self.openwrt_address = user_input[CONF_OPENWRT_ADDREDD]
            self.ring_port = user_input[CONF_RING_PORT]
            self.live_support = user_input[CONF_LIVE_SUPPORT]

            self.mqtt_support = user_input[CONF_MQTT_SUPPORT]
            
            try:
                dnake_stations = user_input.get(CONF_STATIONS, {})
                if dnake_stations:
                    self.dnake_stations = json.loads(dnake_stations)
                    _LOGGER.debug("dnake devices parsed.")
            except Exception as e:
                return self.async_abort(reason=f'dnake devices parse failed: {e}')

            # Proceed to the next step
            if self.mqtt_support:
                return await self.async_step_mqtt()
            else:
                return await self.create_entry()

        # Display the first form with custom title and description
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BUILD, description="Building"): int,
                    vol.Required(CONF_UNIT, description="Unit"): int,
                    vol.Required(CONF_ROOM, description="Room"): int,
                    vol.Optional(CONF_IP_ADDRESS, description="Monitor IP Address"): str,
                    vol.Required(CONF_FAMILY, description="Family ID", default=DEFAULT_FAMILY): int,
                    vol.Required(CONF_ELEV_ID, description="Elev ID", default=DEFAULT_ELEV_ID): int,
                    # vol.Optional(CONF_PORT, description="SIP port", default=SIP_PORT): int,

                    vol.Optional(CONF_OPENWRT_ADDREDD, description="Openwrt Address", default=''): str,
                    vol.Required(CONF_RING_PORT, description="Ring listening port", default=DEFAULT_RING_PORT): int,
                    vol.Optional(CONF_STATIONS, description="Outdoor Stations"): str,

                    vol.Required(CONF_LIVE_SUPPORT, description="Live Support", default=True): bool,

                    vol.Required(CONF_MQTT_SUPPORT, description="MQTT Support", default=False): bool,
                }
            ),
        )

    async def async_step_mqtt(self, user_input=None):
        """Handle the second step (mqtt input)."""
        if user_input is not None:
            self.mqtt_broker = user_input[CONF_MQTT_BROKER]
            self.mqtt_port = user_input[CONF_MQTT_PORT]
            self.mqtt_username = user_input[CONF_MQTT_USERNAME]
            self.mqtt_password = user_input[CONF_MQTT_PASSWORD]
            self.mqtt_keepalive = user_input[CONF_MQTT_KEEPALIVE]
            self.mqtt_topic = user_input[CONF_MQTT_TOPIC]

            # varify mqtt settings if configed
            result = await self._verify_mqtt_credentials(self.mqtt_broker, self.mqtt_port, self.mqtt_username, self.mqtt_password)
            if result['success']:
                _LOGGER.debug("MQTT verified.")
            else:
                return self.async_abort(reason=f'error_code: {result['error_code']}. {result['error_message']}')
            
            return await self.create_entry()

        # Display the second form with custom title and description
        return self.async_show_form(
            step_id="mqtt",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MQTT_BROKER, description="Gateway"): str,
                    vol.Required(CONF_MQTT_PORT, description="Port", default=DEFAULT_MQTT_PORT): int,
                    vol.Required(CONF_MQTT_USERNAME, description="Username"): str,
                    vol.Required(CONF_MQTT_PASSWORD, description="Password"): str,
                    vol.Required(CONF_MQTT_KEEPALIVE, description="Keepalive Interval", default=DEFAULT_MQTT_KEEPALIVE): int,
                    vol.Required(CONF_MQTT_TOPIC, description="Topic", default=DEFAULT_MQTT_TOPIC): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DnakeOptionsFlow(config_entry)

    async def _verify_mqtt_credentials(self, broker, port, username, password, timeout = 30):
        result = {"success": False, "error_code": None, "error_message": ""}

        event = asyncio.Event()
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                result["success"] = True
                result["error_message"] = "Connected."
            else:
                result["error_code"] = rc
                result["error_message"] = f"Connection failed, error code: {rc} (wrong username or password)."
            event.set()

        def on_connect_fail(client, userdata, rc):
            result["success"] = False
            result["error_code"] = rc
            result["error_message"] = f"Connection failed, error code: {rc}."
            event.set()

        client_id = f'{DOMAIN}_{int(time.time())}'
        client = mqtt.Client(client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_connect_fail = on_connect_fail

        client.loop_start()
        client.connect_async(broker, port)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            result["success"] = False
            result["error_message"] = "Connection timed out. This could be due to a network issue or incorrect username/password."

        client.loop_stop()
        client.disconnect()

        return result

class DnakeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def get_dynamic_schema(self):
        dnake_stations = await load_json(STATION_FILENAME)
        schema_dict = {
            vol.Optional(CONF_STATIONS, description="Outdoor Stations", default=json.dumps(dnake_stations, ensure_ascii=False, indent=0)): str,
        }

        return vol.Schema(schema_dict)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            dnake_stations = json.loads(user_input[CONF_STATIONS])
            await save_json(dnake_stations, STATION_FILENAME)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema= await self.get_dynamic_schema(),
        )
