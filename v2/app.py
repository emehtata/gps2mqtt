import gpsd
import paho.mqtt.client as mqtt
import json
import time
import logging
import socket
import uuid
from settings import brokers

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]')

def get_primary_mac():
    # Retrieve the MAC address of the primary network interface
    primary_mac = None
    try:
        primary_mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 8)][::-1])
    except Exception as e:
        logging.error(f"Error getting MAC address: {e}")
    return primary_mac

# Get hostname
hostname = socket.gethostname()

# Generate a unique ID based on the MAC address
mac_address = get_primary_mac()
unique_id = mac_address.replace(":", "") if mac_address else "unknown_id"

# Combined hostname and unique ID
combined_id = f"{hostname}{unique_id}"

# Device tracker configuration data
device_tracker_config = {
    "state_topic": f"gps_module/{combined_id}/state",
    "name": f"GPS Module {combined_id}",
    "payload_home": "online",
    "payload_not_home": "offline",
    "json_attributes_topic": f"gps_module/{combined_id}/attributes",
    "unique_id": f"gps-module-{combined_id}",
    "friendly_name": f"GPS Module {combined_id}"
}

# Initialize the MQTT clients for all brokers
for broker in brokers:
    broker['client'] = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT Broker at {client._host}:{client._port}")
        for broker in brokers:
            if broker['client'] == client:
                broker['connected'] = True
                client.subscribe("homeassistant/status")
                logging.info(f"Subscribed to topic 'homeassistant/status' at {client._host}:{client._port}")

                # Send device tracker configuration data
                client.publish(f"homeassistant/device_tracker/gps_module_{combined_id}/config", json.dumps(device_tracker_config), retain=True)
                logging.info(f"Published configuration to homeassistant/device_tracker/gps_module_{combined_id}/config")
                client.publish(f"gps_module/{combined_id}/state", "online")
                break
    else:
        logging.error(f"Failed to connect to MQTT Broker at {client._host}:{client._port}, return code {rc}")

def on_message(client, userdata, msg):
    logging.info(f"Message received from topic {msg.topic}: {msg.payload.decode()}")
    if msg.payload.decode() == "online":
        logging.info("Received 'online' message, resending device tracker configuration")
        client.publish(f"homeassistant/device_tracker/gps_module_{combined_id}/config", json.dumps(device_tracker_config), retain=True)
        logging.info(f"Resent configuration to homeassistant/device_tracker/gps_module_{combined_id}/config")

# Assign the on_connect and on_message callbacks to each client
for broker in brokers:
    broker['client'].on_connect = on_connect
    broker['client'].on_message = on_message

def connect_to_brokers():
    for broker in brokers:
        try:
            broker['client'].connect(broker['host'], broker['port'], 60)
            broker['client'].loop_start()
        except Exception as e:
            logging.error(f"Error connecting to MQTT Broker at {broker['host']}:{broker['port']}: {e}")

def get_gps_data():
    try:
        packet = gpsd.get_current()
        data = {
            'latitude': packet.lat,
            'longitude': packet.lon,
            'altitude': packet.alt,
            'climb': packet.climb,
            'speed': packet.hspeed * 3.6,  # Convert m/s to km/h
            'bearing': packet.track,
            'time': packet.time,
            'satellites': packet.sats,
            # Add other fields if they are available and needed
        }
        return data
    except Exception as e:
        logging.error(f"Error getting GPS data: {e}")
        return None

def send_data_to_mqtt(data):
    for broker in brokers:
        if broker['connected']:
            try:
                client = broker['client']
                #client.publish(f"gps_module/{combined_id}/state", "home")  # Publish state (assumed to be 'home' for testing)
                client.publish(f"gps_module/{combined_id}/attributes", json.dumps(data))  # Publish attributes
            except Exception as e:
                logging.error(f"Error sending data to MQTT at {broker['host']}:{broker['port']}: {e}")

def main():
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
        time.sleep(1)  # Send data every second

if __name__ == "__main__":
    main()
