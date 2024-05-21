#!/bin/bash

docker run -d --name gps-sim --network=host -v $PWD/sim-files/$1:/sim-files/$1 iotechsys/gps-sim:1.0 -v -c 0.33 /sim-files/$1

