#!/bin/bash

# Get the current time in HHMMSS format
current_time=$(date +"%y%m%d%H%M%S")

# Convert the time to a hexadecimal number
hex_time=$(printf '%010x\n' "$current_time")

# Print the hexadecimal number
# echo "Current time in HHMMSS: $current_time"
echo "$hex_time"
