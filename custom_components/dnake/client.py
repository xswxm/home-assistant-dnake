import time
from datetime import datetime
import json
import socket
import random
import asyncio

import paho.mqtt.client as mqtt

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from . import protocal
from .const import (
    DOMAIN, 
    DEVICE_ID, 
    SENSOR_LAST_EVENT, 

    CONF_BUILD, 
    CONF_UNIT, 
    CONF_ROOM, 
    CONF_ELEV_ID, 
    CONF_IP_ADDRESS, 
    CONF_PORT, 
    
    SIP_PORT, 

    CONF_MQTT_SUPPORT, 
    CONF_MQTT_BROKER, 
    CONF_MQTT_PORT, 
    CONF_MQTT_KEEPALIVE, 
    CONF_MQTT_USERNAME, 
    CONF_MQTT_PASSWORD, 
    CONF_FAMILY, 

    CONF_MQTT_TOPIC, 
)

import logging
_LOGGER = logging.getLogger(__name__)

class DnakeUDPClient:
    def __init__(self, build = 16, unit = 1, room = 2801, ip = '172.16.0.1', port = SIP_PORT) -> None:
        self.build = build
        self.unit = unit
        self.room = room
        self.src_id = f'{build}{unit:0>2d}{room:0>4d}'
        self.src_ip = ip
        self.src_port = port

        self.dst_id = '10019901'
        self.dst_ip = '172.16.0.1'
        self.dst_port = SIP_PORT
        self._registered = False

    def __json2str(self, data: dict):
        return "\r\n".join([f"{key}: {val}" for key, val in data.items()])

    def __dict_to_xml(self, data, tag='params'):
        body = "\n".join([f"\t<{key}>{val}</{key}>" for key, val in data.items()])
        return f'<{tag}>\n{body}\n</{tag}>\n'

    async def send_msg(self, dst_ip, dst_port, msg, recv=False, buffer_len=1024):
        """Send UDP request and receive response"""
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setblocking(False)

            _LOGGER.debug(f"Sent message: {msg}")
            udp_socket.sendto(msg.encode(), (dst_ip, dst_port))

            if recv:
                loop = asyncio.get_running_loop()
                response = await loop.sock_recv(udp_socket, buffer_len)
                
                _LOGGER.debug(f"Receive message: {response.decode()}")
                return response.decode().strip()
            return None
        except (socket.error, asyncio.TimeoutError) as e:
            _LOGGER.debug(f"Error occurred: {e}.")
            return None
        finally:
            udp_socket.close()

    async def join(self, dst_id, dst_ip, dst_port, branch = None, tag = None, call_id = None):
        sip_body = self.__dict_to_xml(protocal.SIP_BODY.JOIN())
        sip_header = self.__json2str(
            protocal.SIP_HEADER.MESSAGE(
                src_id=self.src_id, 
                src_ip=self.src_ip, 
                src_port=self.src_port, 
                dst_id=dst_id, 
                dst_ip=dst_ip, 
                dst_port=dst_port, 
                branch=branch, 
                tag=tag, 
                call_id=call_id, 
                body_length=len(sip_body)
            )
        )
        sip_line = protocal.SIP_LINE.MESSAGE(dst_id=dst_id, dst_ip=dst_ip, dst_port=dst_port)
        sip_message = f'{sip_line}\r\n{sip_header}\r\n\r\n{sip_body}'
        return await self.send_msg(dst_ip=dst_ip, dst_port=SIP_PORT, msg=sip_message)

    async def appoint(self, dst_id, dst_ip, dst_port, elev, direct, build, unit, floor, family = 1, branch = None, tag = None, call_id = None):
        sip_body = self.__dict_to_xml(protocal.SIP_BODY.APPOINT(dst_id=dst_id, dst_ip=dst_ip, dst_port=dst_port, elev=elev, direct=direct, build=build, unit=unit, floor=floor, family=family))
        sip_header = self.__json2str(
            protocal.SIP_HEADER.MESSAGE(
                src_id=self.src_id, 
                src_ip=self.src_ip, 
                src_port=self.src_port, 
                dst_id=dst_id, 
                dst_ip=dst_ip, 
                dst_port=dst_port, 
                branch=branch, 
                tag=tag, 
                call_id=call_id, 
                body_length=len(sip_body)
            )
        )
        sip_line = protocal.SIP_LINE.MESSAGE(dst_id=dst_id, dst_ip=dst_ip, dst_port=dst_port)
        sip_message = f'{sip_line}\r\n{sip_header}\r\n\r\n{sip_body}'
        return await self.send_msg(dst_ip=dst_ip, dst_port=SIP_PORT, msg=sip_message)

    async def unlock(self, dst_id, dst_ip, dst_port, build, unit, floor, family = 1, branch = None, tag = None, call_id = None):
        sip_body = self.__dict_to_xml(protocal.SIP_BODY.UNLOCK(self.src_id, build, unit, floor, family))
        sip_header = self.__json2str(
            protocal.SIP_HEADER.MESSAGE(
                src_id=self.src_id, 
                src_ip=self.src_ip, 
                src_port=self.src_port, 
                dst_id=dst_id, 
                dst_ip=dst_ip, 
                dst_port=dst_port, 
                branch=branch, 
                tag=tag, 
                call_id=call_id, 
                body_length=len(sip_body)
            )
        )
        sip_line = protocal.SIP_LINE.MESSAGE(dst_id=dst_id, dst_ip=dst_ip, dst_port=dst_port)
        sip_message = f'{sip_line}\r\n{sip_header}\r\n\r\n{sip_body}'
        return await self.send_msg(dst_ip=dst_ip, dst_port=SIP_PORT, msg=sip_message)

    async def permit(self, dst_id, dst_ip, dst_port, elev, build, unit, floor, family = 1, branch = None, tag = None, call_id = None):
        sip_body = self.__dict_to_xml(protocal.SIP_BODY.PERMIT(dst_id, dst_ip, dst_port, elev, build, unit, floor, family))
        sip_header = self.__json2str(
            protocal.SIP_HEADER.MESSAGE(
                src_id=self.src_id, 
                src_ip=self.src_ip, 
                src_port=self.src_port, 
                dst_id=dst_id, 
                dst_ip=dst_ip, 
                dst_port=dst_port, 
                branch=branch, 
                tag=tag, 
                call_id=call_id, 
                body_length=len(sip_body)
            )
        )
        sip_line = protocal.SIP_LINE.MESSAGE(dst_id=dst_id, dst_ip=dst_ip, dst_port=dst_port)
        sip_message = f'{sip_line}\r\n{sip_header}\r\n\r\n{sip_body}'
        return await self.send_msg(dst_ip=dst_ip, dst_port=SIP_PORT, msg=sip_message)

class MQTTClient:
    def __init__(self, hass: HomeAssistant, config):
        self.hass = hass
        self.broker = config[CONF_MQTT_BROKER]
        self.port = config[CONF_MQTT_PORT]
        self.keepalive = config[CONF_MQTT_KEEPALIVE]
        self.username = config[CONF_MQTT_USERNAME]
        self.password = config[CONF_MQTT_PASSWORD]
        self.client = None
        self.topic = config[CONF_MQTT_TOPIC]

        self.mqtt_support = config[CONF_MQTT_SUPPORT]

    async def mqtt_connect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

        client_id = f'{DOMAIN}_{int(time.time())}'
        if hasattr(mqtt, 'CallbackAPIVersion'):
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1,
                client_id=client_id
            )
        else:
            self.client = mqtt.Client(client_id=client_id)
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        await self.connect()

    async def connect(self):
        await self.hass.async_add_executor_job(self.client.connect, self.broker, self.port, self.keepalive)
        self.client.loop_start()

    async def disconnect(self):
        self.client.loop_stop()
        await self.hass.async_add_executor_job(self.client.disconnect)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info("Connected to MQTT Broker")
            client.subscribe(self.topic)
        else:
            _LOGGER.error(f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        _LOGGER.warning("Disconnected from MQTT Broker")
        if rc != 0:
            _LOGGER.info("Attempting to reconnect in 5 seconds...")
            self.hass.loop.create_task(self._async_reconnect())

    async def _async_reconnect(self):
        await asyncio.sleep(5)
        await self.mqtt_connect()
        

    def on_message(self, client, userdata, message):
        if message.topic != self.topic:
            _LOGGER.debug(f'MQTT Receviced: {message}')
            return
        msg = message.payload.decode()
        _LOGGER.debug(f'MQTT Message: {msg}')

    def publish(self, topic, msg):
        result = self.client.publish(topic, msg)
        status = result[0]
        if status == 0:
            _LOGGER.debug(f"Publish `{msg}` to `{topic}` topic")
        else:
            _LOGGER.debug(f"Failed to send message to topic {topic}")

class Client(MQTTClient):
    def __init__(self, hass: HomeAssistant, config):
        super().__init__(hass, config)

        self.build = config[CONF_BUILD]
        self.unit = config[CONF_UNIT]
        self.room = config[CONF_ROOM]
        self.src_id = f'{self.build}{self.unit:0>2d}{self.room:0>4d}'
        self.src_ip = config[CONF_IP_ADDRESS]
        self.elev = config[CONF_ELEV_ID]
        self.src_port = config[CONF_PORT]
        self.family = config[CONF_FAMILY]

        self.dnake_client = None

    async def initialize(self):
        if not self.src_ip:
            self.src_ip = await self.update_src_ip()
        self.dnake_client = DnakeUDPClient(
            build=self.build, 
            unit=self.unit, 
            room=self.room, 
            ip=self.src_ip, 
            port=self.src_port
        )
        if self.mqtt_support:
            await self.mqtt_connect()

    async def update_src_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setblocking(False)
            address = ("8.8.8.8", 80)
            
            await asyncio.get_event_loop().sock_connect(s, address)
            sockname = s.getsockname()
            ip = sockname[0]
            # port = sockname[1]
        except Exception as e:
            _LOGGER.error(f"Error: {e}")
            ip = None
        finally:
            s.close()
        return ip

    def update_last_event(self, state_attributes):
        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send,
            self.hass,
            f"{DOMAIN}_{self.hass.data[DOMAIN][DEVICE_ID]}_{SENSOR_LAST_EVENT}",
            state_attributes
        )

    async def process_message(self, message):
        try:
            data = json.loads(message.payload.decode())
            _LOGGER.debug(f"MQTT Received Payload: {data}")
            event = data.get('event', '')
            if event == 'appoint':
                await self.appoint(
                    dst_id=data.get('dst_id'), 
                    dst_ip=data.get('dst_ip'),
                    dst_port=data.get('dst_port', SIP_PORT), 
                    direct=data.get('direct')
                )
            elif event == 'unlock':
                await self.unlock(
                    dst_id=data.get('dst_id'), 
                    dst_ip=data.get('dst_ip'),
                    dst_port=data.get('dst_port', SIP_PORT)
                )
            elif event == 'permit':
                await self.permit(
                    dst_id=data.get('dst_id'), 
                    dst_ip=data.get('dst_ip'),
                    dst_port=data.get('dst_port', SIP_PORT)
                )
            elif event == 'execute':
                await self.execute(
                    data = message
                )
            elif event == 'ring':
                return

        except Exception as e:
            _LOGGER.debug(f'mqtt msg process failed: {e}')

    def on_message(self, client, userdata, message):
        _LOGGER.debug(f"MQTT Received: {message}")
        if message.topic != self.topic:
            return
        self.hass.loop.call_soon_threadsafe(asyncio.create_task, self.process_message(message))

    def __gen_ramdon(self):
        self.branch = f'z9hG4bK{str(random.randint(100000000, 999999999))}'
        self.tag = str(random.randint(1000000000, 9999999999))
        self.call_id = str(random.randint(100000000, 999999999))
        self.line = ''.join(random.choices('0123456789abcdef', k=15))

    async def execute(self, data):
        if isinstance(data, str):
            data = json.loads(data)

        dst_id = data.get('dst_id')
        dst_ip = data.get('dst_ip')
        dst_port = data.get('dst_port', SIP_PORT)
        elev = data.get('elev', 0)
        direct = data.get('direct', 1)
        build = data.get('build', self.build)
        unit = data.get('unit', self.unit)
        floor = data.get('floor', self.room // 100)
        family = data.get('family', self.family)

        if data['event'] == 'appoint':
            await self.appoint_advanced(dst_id, dst_ip, dst_port, elev, direct, build, unit, floor, family)
        elif data['event'] == 'unlock':
            await self.unlock_advanced(dst_id, dst_ip, dst_port, build, unit, floor, family)
        elif data['event'] == 'permit':
            await self.permit_advanced(dst_id, dst_ip, dst_port, elev, build, unit, floor, family)

    async def appoint_advanced(self, dst_id, dst_ip, dst_port, elev, direct, build, unit, floor, family):
        # join
        self.__gen_ramdon()
        await self.dnake_client.join(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            branch = self.branch, 
            tag = self.tag, 
            call_id = self.call_id
        )
        # appoint
        self.__gen_ramdon()
        await self.dnake_client.appoint(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            elev=elev, 
            direct=direct, 
            build=build, 
            unit=unit, 
            floor = floor, 
            family = family, 
            branch = self.branch, 
            tag = self.tag, 
            call_id = self.call_id
        )
        # update sensor
        state_attributes = {
            'event': 'elev_up' if direct == 1 else 'elev_down',
            'src_id': self.src_id,
            'src_ip': self.src_ip,
            'dst_id': dst_id,
            'dst_ip': dst_ip,
            'time': datetime.now().isoformat()
        }
        self.update_last_event(state_attributes)

    async def appoint(self, dst_id, dst_ip, dst_port, direct):
        await self.appoint_advanced(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            elev=self.elev, 
            direct=direct, 
            build=self.build, 
            unit=self.unit, 
            floor = self.room // 100, 
            family = self.family
        )

    async def unlock_advanced(self, dst_id, dst_ip, dst_port, build, unit, floor, family):
        self.__gen_ramdon()
        await self.dnake_client.unlock(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            build=build, 
            unit=unit, 
            floor = floor, 
            family = family, 
            branch = self.branch, 
            tag = self.tag, 
            call_id = self.call_id
        )
        # update sensor
        state_attributes = {
            'event': 'unlock',
            'src_id': self.src_id,
            'src_ip': self.src_ip,
            'dst_id': dst_id,
            'dst_ip': dst_ip,
            'time': datetime.now().isoformat()
        }
        self.update_last_event(state_attributes)

    async def unlock(self, dst_id, dst_ip, dst_port):
        await self.unlock_advanced(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            build=self.build, 
            unit=self.unit, 
            floor = self.room // 100, 
            family = self.family
        )

    async def permit_advanced(self, dst_id, dst_ip, dst_port, elev, build, unit, floor, family):
        self.__gen_ramdon()
        await self.dnake_client.permit(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            elev=elev, 
            build=build, 
            unit=unit, 
            floor = floor, 
            family = family, 
            branch = self.branch, 
            tag = self.tag, 
            call_id = self.call_id
        )
        # update sensor
        state_attributes = {
            'event': 'permit',
            'src_id': self.src_id,
            'src_ip': self.src_ip,
            'dst_id': dst_id,
            'dst_ip': dst_ip,
            'time': datetime.now().isoformat()
        }
        self.update_last_event(state_attributes)

    async def permit(self, dst_id, dst_ip, dst_port):
        await self.permit_advanced(
            dst_id=dst_id, 
            dst_ip=dst_ip, 
            dst_port=dst_port, 
            elev=self.elev, 
            build=self.build, 
            unit=self.unit, 
            floor = self.room // 100, 
            family = self.family
        )
