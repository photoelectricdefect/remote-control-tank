#!/bin/bash

display_usage() {
    printf "\nUsage: $0 [XBOX Name] [Microcontroller Baud Rate]\n"
}

set -e

if [ $# -lt 3 ];
then
    display_usage
    exit 1
fi

DEVICE_NAME="$1"
ESP32_BAUD_RATE="$2"
python3 ./xbox_relay.py "$DEVICE_NAME" "$ESP32_BAUD_RATE"