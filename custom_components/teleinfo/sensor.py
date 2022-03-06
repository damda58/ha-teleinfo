"""
Support for reading Teleinfo data from a serial port.

Teleinfo is a French specific protocol used in electricity smart meters.
It provides real time information on power consumption, rates and current on
a user accessible serial port.

For more details about this platform, please refer to the documentation at
https://www.enedis.fr/sites/default/files/Enedis-NOI-CPT_02E.pdf

Work based on https://github.com/nlamirault

Sample configuration.yaml

    sensor:
    - platform: teleinfo
      name: "Téléinfo"
      serial_port: "/dev/ttyUSB0"
    
    template:
      - sensor:
          - name: "Téléinfo Période tarifaire en cours"
            unique_id: teleinfo_periode_tarifaire_en_cours
            state: >-
              {{ state_attr('sensor.teleinfo', 'PTEC') }}
      - sensor:
          - name: "Téléinfo Intensité souscrite"
            unique_id: teleinfo_intensite_souscite
            unit_of_measurement: A
            device_class: current
            state: >-
              {{ state_attr('sensor.teleinfo', 'ISOUSC') | int }}
      - sensor:
          - name: "Téléinfo Intensité instantanée"
            unique_id: telteinfo_intensite_instantanee
            unit_of_measurement: A
            device_class: current
            state_class: measurement
            state: >-
              {{ state_attr('sensor.teleinfo', 'IINST') | int }}
      - sensor:
          - name: "Téléinfo Puissance apparente"
            unique_id: teleinfo_puissance_apparente
            unit_of_measurement: VA
            device_class: apparent_power
            state_class: measurement
            state: >-
              {{ state_attr('sensor.teleinfo', 'PAPP') | int }}
      - sensor:
          - name: "Téléinfo Index heures creuses"
            unique_id: teleinfo_index_heures_creuses
            unit_of_measurement: kWh
            device_class: energy
            state_class: total_increasing
            state: >-
              {{ state_attr('sensor.teleinfo', 'HCHC') | int / 1000 }}
      - sensor:
          - name: "Téléinfo Index heures pleines"
            unique_id: teleinfo_index_heures_pleines
            unit_of_measurement: kWh
            device_class: energy
            state_class: total_increasing
            state: >-
              {{ state_attr('sensor.teleinfo', 'HCHP') | int / 1000 }}
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA, STATE_CLASS_TOTAL_INCREASING, SensorEntity
from homeassistant.const import (
    CONF_NAME, EVENT_HOMEASSISTANT_STOP, ATTR_ATTRIBUTION, DEVICE_CLASS_ENERGY)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['pyserial-asyncio==0.4']

_LOGGER = logging.getLogger(__name__)

CONF_SERIAL_PORT = 'serial_port'

CONF_ATTRIBUTION = "Provided by EDF Teleinfo."

DEFAULT_NAME = "Serial Teleinfo Sensor"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SERIAL_PORT): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


async def async_setup_platform(hass, config, async_add_entities,discovery_info=None):
    """Set up the Serial sensor platform."""
    name = config.get(CONF_NAME)
    port = config.get(CONF_SERIAL_PORT)
    sensor = SerialTeleinfoSensor(name, port)

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, sensor.stop_serial_read())
    async_add_entities([sensor], True)


class SerialTeleinfoSensor(SensorEntity):
    """Representation of a Serial sensor."""

    def __init__(self, name, port):
        """Initialize the Serial sensor."""
        self._name = name
        self._port = port
        self._serial_loop_task = None
        self._state = None
        self._attributes = {}

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        self._serial_loop_task = self.hass.loop.create_task(
            self.serial_read(self._port, baudrate=1200, bytesize=7,
                             parity='E', stopbits=1, rtscts=1))

    async def serial_read(self, device, **kwargs):
        """Process the serial data."""
        import serial_asyncio
        _LOGGER.debug(u"Initializing Teleinfo")
        reader, _ = await serial_asyncio.open_serial_connection(url=device,
                                                                **kwargs)

        is_over = True

        # First read need to clear the grimlins.
        line = await reader.readline()

        while True:
            line = await reader.readline()
            line = line.decode('ascii').replace('\r', '').replace('\n', '')

            if is_over and ('\x02' in line):
                is_over = False
                _LOGGER.debug(" Start Frame")
                continue

            if (not is_over) and ('\x03' not in line):
                # Don't use strip() here because the checksum can be ' '.
                if len(line.split()) == 2:
                    # The checksum char is ' '.
                    name, value = line.split()
                else:
                    name, value = line.split()[0:2]

                _LOGGER.debug(" Got : [%s] =  (%s)", name, value)
                self._attributes[name] = value

                if name == 'BASE':
                    self._state = int(value)
                continue

            if (not is_over) and ('\x03' in line):
                is_over = True
                self.async_schedule_update_ha_state()
                _LOGGER.debug(" End Frame")
                continue

    async def stop_serial_read(self):
        """Close resources."""
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        self._attributes[ATTR_ATTRIBUTION] = CONF_ATTRIBUTION
        return self._attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def state_class(self):
        return STATE_CLASS_TOTAL_INCREASING # so far no const available in homeassistant core

    @property
    def device_class(self):
        return DEVICE_CLASS_ENERGY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"teleinfo-{self._name.lower()}"

    @property
    def unit_of_measurement(self):
        return "Wh"

    @property
    def icon(self):
        return "mdi:counter"
