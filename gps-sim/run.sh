#!/bin/bash

docker run --rm --name gps-sim --network=host -v $PWD/$1:/sim-files/$1 iotechsys/gps-sim:1.0 -v -c 0.33 /sim-files/$1

