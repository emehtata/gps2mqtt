#!/bin/env python3

import json
import logging
import os
import telnetlib
from time import sleep, time

import gpsd as _gpsd
import paho.mqtt.client as mqtt
from geographiclib.geodesic import Geodesic
from geopy.geocoders import Nominatim

import helpers
# TODO: cli option to enable hw reset switch
# from gpiozero import Button
from settings import (BEARING_BUFFER_SIZE, DEGREE_THRESHOLD,
                      MQTT_RETRY_CONNECT, SPEED_BUFFER_SIZE, SPEED_THRESHOLD,
                      STREET_THRESHOLD, TIME_THRESHOLD, _brokers, _mqtt_topic,
                      _zm_api)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')
if 'DEBUG' in os.environ:
    logging.getLogger().setLevel(logging.INFO)
    if os.environ['DEBUG'] == 2:
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
        self._last_address_fetch = 0

        self._zm_api = _zm_api

        self._speed_buffer = []
        self._bearing_buffer = []

        self._data = {}

        if 'SIMGPS' in os.environ:
            self._mqtt_topic = f"test-{self._mqtt_topic}"

        if (_zm_api['enabled']):
            self.zm_connect()

    def zm_connect(self):
        # Establish a Telnet connection
        try:
            logging.debug(
                f"Connecting telnet {_zm_api['host']}:{_zm_api['port']}")
            self._tn = telnetlib.Telnet(_zm_api['host'], _zm_api['port'])
            logging.debug("Telnet connected!")
        except Exception as e:
            logging.error(
                "Unable to connect zoneminder. Is zmtrigger running?")
            self._tn = None

    def update_buffers(self, speed, bearing):
        self._speed_buffer.append(speed)
        self._bearing_buffer.append(bearing)
        average_speed = -1
        bearing_difference = -1

        if len(self._speed_buffer) > SPEED_BUFFER_SIZE:
            self._speed_buffer.pop(0)
            average_speed = sum(self._speed_buffer) / len(self._speed_buffer)

        if len(self._bearing_buffer) > BEARING_BUFFER_SIZE:
            self._bearing_buffer.pop(0)
            bearing_difference = abs(
                max(self._bearing_buffer) - min(self._bearing_buffer) )

            if bearing_difference > 180:
                bearing_difference = 360 - bearing_difference      

        logging.debug(
            f"speed: {self._speed_buffer} ({average_speed}), bearing: {self._bearing_buffer} ({bearing_difference})")
        return average_speed, bearing_difference


    def update_zm(self, text, retry=True):
        host = self._zm_api['host']
        port = self._zm_api['port']

        i = 0
        for m in self._zm_api['monitors']:
            text = helpers.convert_umlaut_characters(text)
            payload = f"{m[i]}|show||||{text}".encode('utf-8')
            # Send raw text
            try:
                # Sending as ASCII, adding carriage return and newline
                self._tn.write(payload + b'\r\n')
                logging.debug(f"Sent: {payload}")
            except Exception as e:
                logging.error(f"{e} Reconnecting")
                if retry == True:
                    self.zm_connect()
                    self.update_zm(text, retry=False)
                    logging.error(f"Unable to send {payload}")
            i += 1

    def calculate_bearing(self, lat1, lon1):
        # Calculate bearing based on difference to previous coordinates
        try:
            lat2 = self._data['latitude']
            lon2 = self._data['longitude']
        except KeyError:
            logging.debug("uninitialized data")
            return 0
        inverse_data = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        logging.debug(f"{inverse_data}")
        brng = inverse_data['azi1'] + 180
        return brng  

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
    def last_address_fetch(self):
        return self._last_address_fetch

    @last_address_fetch.setter
    def last_address_fetch(self, value):
        self._last_address_fetch = value

    @property
    def zm_api(self):
        return self._zm_api

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, contents):
        self._data = contents


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
    status = helpers.connect_brokers(status)
    speed_limit = 0
    street = city = country = postcode = ''
    previous_speed = -1
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
                    # We may have error. Calculate bearing.
                    bearing = status.calculate_bearing(latitude, longitude)
                    gps_time = packet.time
                    average_speed, bearing_difference = status.update_buffers(
                        speed, bearing)

                    if ( (bearing_difference >= DEGREE_THRESHOLD and status.last_address_fetch - time() > BEARING_BUFFER_SIZE) or 
                         (time() - status.last_address_fetch > STREET_THRESHOLD) or
                         (average_speed > 0 and (time() - previous_time >= TIME_THRESHOLD)) or 
                         (average_speed < 0) ):
                        address = helpers.perform_reverse_geocoding(
                            status, latitude, longitude)
                        logging.info(f"{address}")
                        if address:
                            street = address.get('road', '')
                            city = address.get('city', '')
                            postcode = address.get('postcode', '')
                            country = address.get('country_code', '')
                            suburb = address.get('suburb')
                            status.last_address_fetch = time()
                        speed_limit = helpers.get_speed_limit(latitude, longitude)

                    if hasattr(packet, 'alt') and hasattr(packet, 'climb'):
                        altitude = packet.alt
                        climb = packet.climb
                    else:
                        altitude = climb = 0

                    # Create a JSON object
                    status.data = {
                        'latitude': latitude,
                        'longitude': longitude,
                        'altitude': altitude,
                        'climb': climb,
                        'speed': round(average_speed, 1),
                        'bearing': bearing,
                        'gps_accuracy': packet.position_precision()[0],
                        'street': street,
                        'postcode': postcode,
                        'suburb': suburb,
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
                    logging.info(f"{status.data}")
                    # Convert the JSON object to a string
                    json_data = json.dumps(status.data)
                    previous_time = time()
                    # Publish the JSON data to each MQTT broker
                    logging.debug(f"Brokers: {status.brokers}")

                    if (status.zm_api['enabled'] and round(previous_speed) != round(average_speed)):
                        status.update_zm(
                            f"{str(round(speed)).rjust(3)} km/h {street} {postcode} {suburb} {city} {country}")
                        previous_speed = average_speed

                    for brokers in status.brokers:
                        if status.last_connect_fail > 0 and time() - status.last_connect_fail > MQTT_RETRY_CONNECT:
                            status = helpers.retry_mqtt_connect(status)
                        logging.debug(f"Topic: {status.mqtt_topic}")
                        brokers['client'].publish(status.mqtt_topic, json_data)

                    if 'DEBUG' in os.environ:
                        helpers.output_display(status)
            else:
                logging.info(f"Waiting for valid data. ({packet.mode} < 2)")
            sleep(1)
        except KeyboardInterrupt:
            # Exit the loop if Ctrl+C is pressed
            break
        # except Exception as e:
        #    logging.error(f"Unhandled exception {e}")
        #    sleep(1)


if __name__ == '__main__':
    status = Status()
    main_loop(status)
