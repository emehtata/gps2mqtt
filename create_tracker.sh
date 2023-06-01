#!/bin/bash

broker="192.168.7.8"

mosquitto_pub -h $broker -t homeassistant/device_tracker/gps_module/config -m '{"state_topic": "gps_module/state", "name": "gps_module", "payload_home": "home", "payload_not_home": "not_home", "json_attributes_topic": "gps_module/attributes", "unique_id": "gps-module", "friendly_name": "GPS Module" }'
