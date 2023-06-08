#!/usr/bin/env python3
import logging
from datetime import datetime
from time import time

import paho.mqtt.client as mqtt
import requests

# Function to perform reverse geocoding


def perform_reverse_geocoding(status, latitude, longitude):
    location = status.geolocator.reverse((latitude, longitude))
    if location:
        address = location.raw.get('address', {})
        logging.info("Address found")
        return address
    return None


def get_speed_limit(latitude, longitude):
    url = f"https://overpass-api.de/api/interpreter?data=[out:json];way[maxspeed](around:30,{latitude},{longitude});out;"
    response = requests.get(url)
    logging.debug(f"{response}")
    if response.status_code == 200:
        json_data = response.json()
        logging.debug(f"{json_data}")
        elements = json_data.get('elements', [])
        speed_limit = 0
        for element in elements:
            tags = element.get('tags', {})
            maxspeed = tags.get('maxspeed')
            if maxspeed:
                speed_limit = maxspeed
                break
        return speed_limit
    else:
        return 0


def convert_umlaut_characters(text):
    conversion_table = {
        'Å': 'A', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        'å': 'a', 'ä': 'a', 'ö': 'o', 'ü': 'u'
    }
    return ''.join(conversion_table.get(char, char) for char in text)


def update_zm(status, text, retry=True):
    host = status.zm_api['host']
    port = status.zm_api['port']

    i = 0
    for m in status.zm_api['monitors']:
        text = convert_umlaut_characters(text)
        payload = f"{m[i]}|show||||{text}".encode('utf-8')
        # Send raw text
        try:
            # Sending as ASCII, adding carriage return and newline
            status.tn.write(payload + b'\r\n')
            logging.debug(f"Sent: {payload}")
        except Exception as e:
            logging.error(f"{e} Reconnecting")
            if retry == True:
                status.zm_connect()
                update_zm(status, text, retry=False)
                logging.error(f"Unable to send {payload}")

        i += 1

    return status


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker")
    else:
        logging.error("Failed to connect, return code: ", rc)


def on_publish(client, userdata, mid):
    logging.debug(f"Message published {mid}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.error("Unexpected MQTT disconnection.")


def retry_mqtt_connect(status):
    conn_ok = True
    b = 0
    for broker in status.brokers:
        try:
            if not broker['connected']:
                status.brokers[b]['client'].connect(
                    broker['host'], port=broker['port'])
                status.brokers[b]['client'].loop_start()
                status.brokers[b]['connected'] = True
                logging.info(
                    f"Connection successful: {broker['host']}:{broker['port']}")
        except OSError:
            logging.error(
                f"Could not connect: {broker['host']}:{broker['port']}")
            status.last_connect_fail = time()
            conn_ok = False
        b += 1

    if conn_ok:
        logging.info(f"All brokers connected! {status.brokers}")
        status.last_connect_fail = 0
        status.all_connected = True
    else:
        logging.error(f"Retry failed: {status.brokers}")

    return status


def connect_brokers(status):
    i = 0
    b = 0
    for broker in status.brokers:
        try:
            status.brokers[b]['client'] = mqtt.Client()
            status.brokers[b]['client'].on_connect = on_connect
            status.brokers[b]['client'].on_publish = on_publish
            status.brokers[b]['client'].connect(
                broker['host'], port=broker['port'])
            status.brokers[b]['client'].loop_start()
            status.brokers[b]['connected'] = True
            i += 1
        except OSError:
            logging.error(
                f"Could not connect: {broker['host']}:{broker['port']}")
            status.last_connect_fail = time()
        b += 1

    if i == 0:
        logging.error(
            f"Could not connect any of the MQTT brokers: {status.brokers}")
        raise OSError

    if i == b:
        logging.info(f"All brokers connected!")
        status.last_connect_fail = 0
        status.all_connected = True

    logging.debug(f"Brokers: {status.brokers}")

    return status


def decimal_to_dms(decimal_degrees, unit='°'):
    degrees = int(decimal_degrees)
    decimal_minutes = abs(decimal_degrees - degrees) * 60
    minutes = int(decimal_minutes)
    seconds = round((decimal_minutes - minutes) * 60)

    return f"{degrees}{unit}{minutes}'{seconds}\""


def get_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time


def output_display(status):
    display_rows = {}
    jsondata = status.data
    if 'street' in jsondata and 'city' in jsondata:
        display_rows["A"] = f"{jsondata['street']}, {jsondata['city']}"
    if 'latitude' in jsondata and 'longitude' in jsondata:
        display_rows["B"] = f"{decimal_to_dms(jsondata['latitude']).ljust(8)} {decimal_to_dms(jsondata['longitude'])}"
        display_rows["C"] = f"{str(round(jsondata['speed'])).rjust(3)} km/h ({jsondata['speed_limit']}) {str(round(jsondata['bearing'])).rjust(3)}°"
    if 'satellites' in jsondata:
        mqttconn = "OK"
        if jsondata['mqtt_fail'] != 0:
            mqttconn = "NOK"
        display_rows["D"] = f"S{jsondata['satellites']} {mqttconn} {get_time()}"
    if 'temperature' in jsondata:
        display_rows["E"] = f"{jsondata['temperature']}°C {jsondata['humidity']}%"
        logging.info(f"Temp and time: {jsondata['temperature']}")
    i = 0
    rows = display_rows
    # logging.info(f"Display {di}: {rows}")
    logging.info(".-------------------.")
    for r in rows:
        logging.info(f"|{rows[r].ljust(19)}|")
        i += 1
    # draw.text((0, step_size * i), get_time(), font=font_size, fill="white")
    logging.info("'-------------------'")
