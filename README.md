# GPS tracker

Send device GPS location data to MQTT broker in Home Assistant attribute format.

Designed and tested in Raspberry Pi 2 Raspberry Pi OS. Python version may affect functionality.

## Files

    gps2mqtt.py - Read data from gpsd and send it to MQTT broker
    settings.py - Modify your MQTT broker settings and adjust THRESHOLD values

    requirements.txt - python modules required to run script

    create_tracker.sh - Helper script to create device_tracker in Home Assistant

    switch/ - utility service to monitor a microswitch to run 'sudo service supervisor restart'

## Requirements

`gpsd` must be installed and able to produce GPS data

Install required modules:

    pip install -r requirements.txt

