#!/usr/bin/env bash
# Continuously print CPU temperature every second

THRESHOLD=70

clear
echo "Monitoring CPU Temperature..."

while true; do
    # Example output: temp=47.8'C → extract the number before the apostrophe
    raw=$(vcgencmd measure_temp)
    temp=$(echo "$raw" | grep -oP '[0-9.]+')

    if (( $(echo "$temp > $THRESHOLD" | bc -l) )); then
        # Red
        echo -ne "\r\033[31m$raw\033[0m"
    else
        # Normal
        echo -ne "\r$raw"
    fi

    sleep 1
done
