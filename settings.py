# Constants
SPEED_THRESHOLD = 3 # km/h
DEGREE_THRESHOLD = 30  # Minimum bearing change (degrees)
TIME_THRESHOLD = 30  # Minimum time threshold (seconds)
MQTT_RETRY_CONNECT = 10 # Seconds to wait for next retry to connect to MQTT broker

# MQTT broker details
_brokers = [
    {'host': '192.168.7.8', 'port': 1883, 'client': None, 'connected': False },
    {'host': 'localhost', 'port': 1883, 'client': None, 'connected': False }
]
_mqtt_topic = 'gps_module/attributes'

