#!/bin/env python3

import json
import logging
import os
import requests
import telnetlib
from time import sleep, time

import gpsd as _gpsd
import paho.mqtt.client as mqtt
from geopy.geocoders import Nominatim
# TODO: cli option to enable hw reset switch
# from gpiozero import Button
from settings import DEGREE_THRESHOLD, SPEED_THRESHOLD, TIME_THRESHOLD, MQTT_RETRY_CONNECT, _brokers, _mqtt_topic, _zm_api

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')
if 'DEBUG' in os.environ:
    logging.getLogger().setLevel(logging.DEBUG)

class Status:
    def __init__(self):
        self._geolocator = Nominatim(user_agent='ha_address_finder')

        # Connect to gpsd
        self.gpsd.connect()

        # settings
        self._brokers = _brokers
        self._mqtt_topic = _mqtt_topic

        self._last_connect_fail = 0

        self._zm_api = _zm_api

        if(_zm_api['enabled']):
            self.zm_connect()

    def zm_connect(self):
        # Establish a Telnet connection
        try:
            logging.debug(f"Connecting telnet {_zm_api['host']}:{_zm_api['port']}")
            self._tn = telnetlib.Telnet(_zm_api['host'], _zm_api['port'])
            logging.debug("Telnet connected!")
        except Exception as e:
            logging.error("Unable to connect zoneminder. Is zmtrigger running?")
            self._tn = None

    def update_zm(self, text, retry=True):
        host = self._zm_api['host']
        port = self._zm_api['port']

        i = 0
        for m in self._zm_api['monitors']:
            text = convert_umlaut_characters(text)
            payload = f"{m[i]}|show||||{text}".encode('utf-8')
            # Send raw text
            try:
                self._tn.write(payload + b'\r\n')  # Sending as ASCII, adding carriage return and newline
                logging.debug(f"Sent: {payload}")
            except Exception as e:
                logging.error(f"{e} Reconnecting")
                if retry == True:
                    self.zm_connect()
                    self.update_zm(text, retry=False)
                    logging.error(f"Unable to send {payload}")
            i += 1

    # Getter for 'gpsd' object
    @property
    def gpsd(self):
        return _gpsd

    # Getter for 'tn' object
    @property
    def tn(self):
        return self._tn

    # Getter for 'geolocator' object
    @property
    def geolocator(self):
        return self._geolocator

    @property
    def brokers(self):
        # logging.debug(f"brokers: {self._brokers}")
        return self._brokers

    @property
    def mqtt_topic(self):
        return self._mqtt_topic

    @property
    def last_connect_fail(self):
        # logging.debug(f"last_connect_fail: {self._last_connect_fail}")
        return self._last_connect_fail

    @last_connect_fail.setter
    def last_connect_fail(self, value):
        self._last_connect_fail = value

    @property
    def zm_api(self):
        return self._zm_api

# Function to perform reverse geocoding


def perform_reverse_geocoding(status, latitude, longitude):
    location = status.geolocator.reverse((latitude, longitude))
    if location:
        address = location.raw.get('address', {})
        return address
    return None

def get_speed_limit(latitude, longitude):
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={longitude-0.001},{latitude-0.001},{longitude+0.001},{latitude+0.001}"
    response = requests.get(url)
    if response.status_code == 200:
        xml_data = response.content
        xml_string = xml_data.decode('utf-8')
        speed_limit = 0
        # logging.debug(xml_string)
        for line in xml_string.splitlines():
            if "<tag k=\"maxspeed\" v=" in line:
                speed_limit = line.split("\"")[3]
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
            status.tn.write(payload + b'\r\n')  # Sending as ASCII, adding carriage return and newline
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

# Main loop to continuously read GPS data

def retry_mqtt_connect(status):
    conn_ok = True
    b = 0
    for broker in status.brokers:
        try:
            if not broker['connected']:
                status.brokers[b]['client'].connect(broker['host'], port=broker['port'])
                status.brokers[b]['client'].loop_start()
                status.brokers[b]['connected'] = True
                logging.info(f"Connection successful: {broker['host']}:{broker['port']}")
        except OSError:
            logging.error(
                f"Could not connect: {broker['host']}:{broker['port']}")
            status.last_connect_fail = time()
            conn_ok = False
        b += 1

    if conn_ok:
        logging.debug(f"All brokers connected! {status.brokers}")
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
            status.brokers[b]['client']=mqtt.Client()
            status.brokers[b]['client'].on_connect = on_connect
            status.brokers[b]['client'].on_publish = on_publish
            status.brokers[b]['client'].connect(broker['host'], port=broker['port'])
            status.brokers[b]['client'].loop_start()
            status.brokers[b]['connected'] = True
            i += 1
        except OSError:
            logging.error(
                f"Could not connect: {broker['host']}:{broker['port']}")
            status.last_connect_fail = time()
        b += 1

    if i == 0:
        logging.error(f"Could not connect any of the MQTT brokers: {status.brokers}")
        raise OSError

    if i == b:
        logging.debug(f"All brokers connected!")
        status.last_connect_fail = 0
        status.all_connected = True

    logging.debug(f"Brokers: {status.brokers}")

    return status
'''
def restart_program():
    python = sys.executable
    os.execv(__file__, sys.argv)

# Function to be called when the microswitch is pressed
def button_pressed():
    print("Microswitch pressed. Restarting.")
    restart_program()
'''
def main_loop(status):
    status = connect_brokers(status)
    speed_limit = 0
    street = city = country = postcode = ''
    bearing_time = None
    previous_speed = -1
    previous_bearing = None
    previous_time = None
    '''
    # Define the GPIO pin number
    GPIO_PIN = 17

    # Create a Button object for the GPIO pin
    button = Button(GPIO_PIN)

    # Assign the button_pressed function to the Button object's `when_pressed` event
    button.when_pressed = button_pressed
    '''
    while True:
        try:
            # Wait for new data to be received
            packet = status.gpsd.get_current()
            # Check if the data is valid
            if packet.mode >= 2:  # Valid data in 2D or 3D fix
                if hasattr(packet, 'lat') and hasattr(packet, 'lon'):
                    # Get latitude, longitude, speed, and bearing
                    latitude = packet.lat
                    longitude = packet.lon
                    speed = packet.hspeed * 3.6
                    if speed < SPEED_THRESHOLD:
                        speed = 0
                    bearing = packet.track
                    gps_time = packet.time

                    if (previous_bearing is None or
                        (speed > 0 and abs(bearing - previous_bearing) >= DEGREE_THRESHOLD) or
                            (speed > 0 and previous_time is not None and time() - previous_time >= TIME_THRESHOLD)):
                        address = perform_reverse_geocoding(
                            status, latitude, longitude)
                        if address:
                            street = address.get('road', '')
                            city = address.get('city', '')
                            postcode = address.get('postcode', '')
                            country = address.get('country_code', '')
                        speed_limit = get_speed_limit(latitude, longitude)
                        previous_bearing = bearing
                        bearing_time = time()

                    if hasattr(packet, 'alt') and hasattr(packet, 'climb'):
                        altitude = packet.alt
                        climb = packet.climb
                    else:
                        altitude = climb = 0

                    # Create a JSON object
                    data = {
                        'latitude': latitude,
                        'longitude': longitude,
                        'altitude': altitude,
                        'climb': climb,
                        'speed': round(speed,1),
                        'bearing': bearing,
                        'gps_accuracy': packet.position_precision()[0],
                        'street': street,
                        'postcode': postcode,
                        'city': city,
                        'country': country,
                        'time': gps_time,
                        'satellites': packet.sats,
                        'mqtt_fail': status.last_connect_fail,
                        'speed_limit': speed_limit,
                        'altitude': altitude,
                        'climb': climb,
                        'room': 'car'
                    }
                    logging.debug(f"{data}")
                    # Convert the JSON object to a string
                    json_data = json.dumps(data)
                    if bearing_time is None or time() - bearing_time > 5:
                        logging.debug(f"Storing previous bearing.")
                        previous_bearing = bearing
                        bearing_time = time()
                    previous_time = time()
                    # Publish the JSON data to each MQTT broker
                    logging.debug(f"Brokers: {status.brokers}")

                    if ( status.zm_api['enabled'] and round(previous_speed) != round(speed) ) or 'DEBUG' in os.environ:
                        status.update_zm(f"{str(round(speed)).rjust(3)} km/h {street} {postcode} {city}")
                        previous_speed = speed

                    for brokers in status.brokers:
                        if status.last_connect_fail > 0 and time() - status.last_connect_fail > MQTT_RETRY_CONNECT:
                            status = retry_mqtt_connect(status)
                        brokers['client'].publish(status.mqtt_topic, json_data)
            else:
                logging.info(f"Waiting for valid data. ({packet.mode} < 2)")
            sleep(1)
        except KeyboardInterrupt:
            # Exit the loop if Ctrl+C is pressed
            break
        #except Exception as e:
        #    logging.error(f"Unhandled exception {e}")
        #    sleep(1)


if __name__ == '__main__':
    status = Status()
    main_loop(status)
