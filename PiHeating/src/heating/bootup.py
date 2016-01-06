#!/usr/bin/env python

import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import time

logger = logging.getLogger("bootup")
level = logging.getLevelName(logging.INFO)
logger.setLevel(level)
#self.logger.setLevel(logging.INFO)

fh = RotatingFileHandler("bootup.log",
                         maxBytes=1000000, # 1Mb I think
                         backupCount=5)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("bootup.py has started")


try:
    args = sys.argv[1:][0]
except:
    args = 0
    
logger.info("bootup passed args %s" % (args))


process_name = "main.py"

p = subprocess.Popen(['ps', '-Af'], stdout=subprocess.PIPE)
out, err = p.communicate()

logger.debug("pid search results %s" % (out))

tmp = os.popen("ps -Af").read()

if process_name not in tmp[:]:
    logger.info("The process is not running. Lets Restart")
    
    """Use nohop to run as daemon"""
    
    newprocess = "nohup sudo python %s &" %(process_name)
    os.system(newprocess)
    
elif args == '-r':
    logger.info("Forced restart requested")
    for line in out.splitlines():
        if process_name in line:
            logger.info("Process found %s so killing" % (line))
            pid = int(line.split(None, 2)[1])
            #os.kill(int(pid), 0)
            os.system('sudo kill %d' % (pid))
            
    time.sleep(2)
    logger.info("Now restarting the process %s" %(process_name))
    newprocess = "nohup sudo python %s &" %(process_name)
    os.system(newprocess)
    
else:
    logger.info("Process is already running")
    
    
    