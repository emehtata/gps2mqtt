import logging
import ssl

import paho.mqtt.client as mqtt

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code " + str(rc))
    client.subscribe("weather-v2/12083/#")

def on_message(client, userdata, msg):
    logging.info("Received message: " + msg.payload.decode())

def on_subscribe(client, userdata, mid, granted_qos):
    logging.info("Subscribed to topic")

client = mqtt.Client(transport="websockets")

client.tls_set_context(ssl.create_default_context())

client.on_connect = on_connect

client.on_message = on_message

client.on_subscribe = on_subscribe

client.ws_set_options(path="/mqtt", headers=None)


client.connect("tie.digitraffic.fi", 443, 30)

client.loop_forever()
