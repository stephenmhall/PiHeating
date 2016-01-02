#!/usr/bin/env python

import os

process_name = "main.py"

tmp = os.popen("ps -Af").read()

if process_name not in tmp[:]:
    print "The process is not running. Lets Restart"
    
    """Use nohop to run as daemon"""
    
    newprocess = "nohup sudo python %s &" %(process_name)
    os.system(newprocess)
    
else:
    print "process is running."
    
    