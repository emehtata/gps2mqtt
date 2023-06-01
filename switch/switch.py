#!/bin/env python3
import logging
import subprocess
import asyncio
import os
from gpiozero import Button

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
if 'DEBUG' in os.environ:
    logging.getLogger().setLevel(logging.DEBUG)

# Define the GPIO pin number
GPIO_PIN = 17

# Create a Button object for the GPIO pin
button = Button(GPIO_PIN)

# Function to be called when the microswitch is pressed
def button_pressed():
    logging.info("Microswitch pressed!")
    subprocess.run(['sudo', 'service', 'supervisor', 'restart'])
    subprocess.run(['sudo', 'service', 'raspicam', 'restart'])
    return "Supervisor restarted!"

# Assign the button_pressed function to the Button object's `when_pressed` event
button.when_pressed = button_pressed

# Keep the program running until interrupted
loop = asyncio.get_event_loop()
try:
    logging.info("Entering event loop.")
    loop.run_forever()
finally:
    logging.info("Exit requested.")
    loop.close()

logging.info("Exited.")