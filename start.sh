#!/bin/bash

display_usage() {
    printf "\nUsage: $0 [XBOX Name]\n"
}

set -e

if [ $# -lt 2 ];
then
    display_usage
    exit 1
fi

DEVICE_NAME="$1"
python3 ./tank_control.py "$DEVICE_NAME"