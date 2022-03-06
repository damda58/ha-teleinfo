Home ASsistant Teleinfo

French Teleinfo integration for Home Assistant.
Needs a serial dongle/interface.

## How to install:

### HACS
Add this repo (https://github.com/jeremiedmsn/ha-teleinfo) to the HACS store and install from there.

### local install
Put in "custom_components" folder located in hass.io inside the config folder.
(The 2 .py file must be config/custom_components/ha-teleinfo)

## Sample Configuration

Put this inside configuration.yaml in config folder of hass.io

```yaml
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
```

(use the serial_port of your interface)