#!/bin/bash

sudo cpufreq-set -c 0 -g conservative
sudo service gpsd restart
. ../.venv/bin/activate && python3 app.py
