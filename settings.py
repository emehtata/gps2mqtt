# Constants
SPEED_THRESHOLD = 1 # km/h
DEGREE_THRESHOLD = 30  # Minimum bearing change (degrees)
TIME_THRESHOLD = 30  # Minimum time threshold (seconds)
MQTT_RETRY_CONNECT = 10 # Seconds to wait for next retry to connect to MQTT broker
BUFFERS_SIZE = 3 # Buffer size for speed and bearing

# MQTT brokers details
_brokers = [
    {'host': '192.168.7.8', 'port': 1883, 'client': None, 'connected': False },
    {'host': 'localhost', 'port': 1883, 'client': None, 'connected': False }
]
_mqtt_topic = 'gps_module/attributes'

# Zoneminder overlay
_zm_api = {
    "host": "192.168.7.8",
    "port": "6802",
    "enabled": True,
    "monitors": [ "3" ]
}