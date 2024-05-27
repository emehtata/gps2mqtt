#!/bin/bash

# Get the current time in HHMMSS format
cy=$(( $(date +"%Y")-2023 ))
current_time=${cy}$(date +"%m%d%H%M")

# Convert the time to a hexadecimal number
hex_time=$(printf '%08x\n' "$current_time")

# Print the hexadecimal number
# echo "Current time in HHMMSS: $current_time"
echo "$hex_time"
