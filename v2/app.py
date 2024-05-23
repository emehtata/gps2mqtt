import gpsd
import paho.mqtt.client as mqtt
import json
import time
import logging
import socket
import signal
import sys
from settings import brokers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]')

def get_version():
    """
    Reads the version of the application from the VERSION file.

    Returns:
        str: The version string, or "unknown" if the file cannot be read.
    """
    try:
        with open("VERSION", "r") as version_file:
            return version_file.read().strip()
    except Exception as e:
        logging.error(f"Error reading VERSION file: {e}")
        return "unknown"

VERSION = get_version()
fix = 0
gps_error = False

# Get the hostname of the device
hostname = socket.gethostname()

# Combine hostname with a unique ID
combined_id = f"{hostname}"

# Load configuration from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Device tracker configuration data
device_tracker_config = {
    "state_topic": config['mqtt_topics']['state'].format(combined_id=combined_id),
    "name": f"GPS Module {hostname}",
    "json_attributes_topic": config['mqtt_topics']['attributes'].format(combined_id=combined_id),
    "unique_id": f"gps-module-{combined_id}",
    "friendly_name": f"GPS Module {hostname}"
}

def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    The callback function for when the client receives a CONNACK response from the server.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        flags (dict): Response flags sent by the broker.
        rc (int): The connection result.
    """
    if reason_code == 0:
        logging.info(f"Connected to MQTT Broker at {client._host}:{client._port}")
        for broker in brokers:
            if broker['client'] == client:
                broker['connected'] = True
                client.subscribe(config['mqtt_topics']['homeassistant_status'])
                logging.info(f"Subscribed to topic '{config['mqtt_topics']['homeassistant_status']}' at {client._host}:{client._port}")
                client.publish(f"homeassistant/device_tracker/gps_module_{combined_id}/config", json.dumps(device_tracker_config), retain=True)
                logging.info(f"Published configuration to homeassistant/device_tracker/gps_module_{combined_id}/config")
                break
    else:
        logging.error(f"Failed to connect to MQTT Broker at {client._host}:{client._port}, return code {reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    """
    The callback function for when the client disconnects from the broker.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        rc (int): The disconnection result.
    """
    logging.warning(f"Disconnected from MQTT Broker at {client._host}:{client._port}.")
    for broker in brokers:
        if broker['client'] == client:
            broker['connected'] = False
            break

def on_message(client, userdata, msg, properties=None):
    """
    The callback function for when a PUBLISH message is received from the server.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        msg (mqtt.MQTTMessage): An instance of MQTTMessage, which contains topic, payload, qos, retain.
    """
    logging.info(f"Message received from topic {msg.topic}: {msg.payload.decode()}")
    if msg.payload.decode() == "online":
        logging.info("Received 'online' message, resending device tracker configuration")
        client.publish(f"homeassistant/device_tracker/gps_module_{combined_id}/config", json.dumps(device_tracker_config), retain=True)
        logging.info(f"Resent configuration to homeassistant/device_tracker/gps_module_{combined_id}/config")

def connect_to_brokers():
    """
    Connects to all MQTT brokers specified in the settings.
    """
    for broker in brokers:
        try:
            broker['client'] = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            broker['client'].on_connect = on_connect
            broker['client'].on_disconnect = on_disconnect
            broker['client'].on_message = on_message
            broker['client'].reconnect_delay_set(min_delay=1, max_delay=120)
            broker['client'].connect_async(broker['host'], broker['port'], 10)
            broker['client'].loop_start()
        except Exception as e:
            logging.error(f"Error connecting to MQTT Broker at {broker['host']}:{broker['port']}: {e}")

def get_gps_data():
    """
    Retrieves the current GPS data packet from GPSD.

    Returns:
        dict: A dictionary containing GPS data such as latitude, longitude, altitude, etc.
        None: If there is an error or no GPS fix is available.
    """
    global fix, gps_error
    try:
        packet = gpsd.get_current()
        if gps_error:
            logging.info("GPS active")
            gps_error = False
        if packet.mode < 2:  # 2D fix
            if packet.mode != fix:
                logging.warning(f"No GPS fix available (Mode: {packet.mode}).")
                fix = packet.mode
            return None
        data = {
            'latitude': packet.lat,
            'longitude': packet.lon,
            'altitude': packet.alt,
            'climb': packet.climb,
            'speed': packet.hspeed * 3.6,  # Convert m/s to km/h
            'bearing': packet.track,
            'time': packet.time,
            'satellites': packet.sats,
            'sats_valid': packet.sats_valid,
            'gps_accuracy': packet.position_precision()[0],
        }
        return data
    except Exception as e:
        if not gps_error:
            logging.error(f"Error getting GPS data: {e}")
            gps_error = True
        return None

def send_data_to_mqtt(data):
    """
    Sends GPS data to all connected MQTT brokers.

    Args:
        data (dict): The GPS data to send.
    """
    for broker in brokers:
        if broker['connected']:
            try:
                client = broker['client']
                client.publish(config['mqtt_topics']['attributes'].format(combined_id=combined_id), json.dumps(data))
                logging.info(f"Data sent to MQTT at {broker['host']}:{broker['port']}")
            except Exception as e:
                logging.error(f"Error sending data to MQTT at {broker['host']}:{broker['port']}: {e}")

def signal_handler(sig, frame):
    """
    Handles graceful shutdown on receiving SIGINT or SIGTERM signals.
    """
    logging.info('Graceful shutdown initiated...')
    for broker in brokers:
        try:
            if broker['client']:
                broker['client'].disconnect()
                broker['client'].loop_stop()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
    sys.exit(0)

def main():
    """
    The main function to start the GPS to MQTT application.
    """
    logging.info(f"Starting GPS to MQTT application version {VERSION}")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Connect to all brokers
    connect_to_brokers()

    # Wait for at least one MQTT connection
    while not any(broker['connected'] for broker in brokers):
        time.sleep(1)

    # Connect to the local gpsd
    gpsd.connect()

    while True:
        gps_data = get_gps_data()
        if gps_data:
            logging.info(f"Sending data: {gps_data}")
            send_data_to_mqtt(gps_data)
        time.sleep(config['sleep_interval'])  # Send data every interval specified in config

if __name__ == "__main__":
    main()
