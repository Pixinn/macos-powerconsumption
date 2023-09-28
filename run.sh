#!/bin/bash

# Launch powermetrics in the background
sudo  powermetrics -i 1000 --samplers cpu_power,gpu_power -a --hide-cpu-duty-cycle --show-usage-summary --show-extra-power-info > powermetric-logs/Firefox-VP9.txt  &
sleep 30

# Run the script that sends commands to the browser
osascript launch-test.scpt
sleep 30

# Find and kill the powermetrics process by name
sudo pkill powermetrics

