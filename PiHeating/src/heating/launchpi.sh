#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
# call with one parameter -r for reboot -c for check


cd /
cd home/pi/heating
sudo python bootup.py "$1"
cd /
