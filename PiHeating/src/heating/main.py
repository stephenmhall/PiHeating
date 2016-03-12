#!/usr/bin/python
'''
Created on 1 Nov 2015

@author: stephen H

test change

'''
from __future__ import division

__updated__ = "2016-03-12"

import logging
from logging.handlers import RotatingFileHandler
import threading
import multiprocessing
import neopixelserial
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from requesthandler import MyRequestHandler
from heatinggpio import setupGPIO, buttonCheckHeat, hBeat
from database import DbUtils
from variables import Variables
from sys import platform as _platform
from os import system
import hardware

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()



class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests is separate thread"""
    
class Main():
    
    def __init__(self):
        #Initialise the Logger
        
        logLevel = Variables().readVariables(['LoggingLevel']).rstrip('\r')
        useNeoPixel = Variables().readVariables(['UseNeoPixel'])
        self.logger = logging.getLogger("main")
        level = logging.getLevelName(logLevel)
        self.logger.setLevel(level)
        #self.logger.setLevel(logging.INFO)
        
        fh = RotatingFileHandler("heating.log",
                                 maxBytes=1000000, # 1Mb I think
                                 backupCount=5)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Main has started __init__ has run logger level is %s" % logLevel)
        
        try:
            cube = DbUtils().getCubes()
            self.logger.info("Database OK cube %s found" % (cube[1]))
        except Exception, err:
            DbUtils().initialiseDB()
            self.logger.exception("Database Initialised %s" % err)
        self.logger.info("Free Memory at Boot %s MB" % hardware.getRAM())
        self.logger.info("CPU Usage at Boot %s" % hardware.getCPUUse())
        
        # Start Serial connection worker if using NeoPixel
        if useNeoPixel:
            arduino = neopixelserial.SerialProcess(input_queue, output_queue)
            arduino.daemon = True
            arduino.start()
        # Or start the GPIO
        else:
            setupGPIO()
        
        # Start Web UI
        self.startKioskServer()
        
        # Start Main Loop
        self.doLoop()
        
               
            
    def doLoop(self):
        checkInterval, boiler_enabled = Variables().readVariables(['Interval', 'BoilerEnabled'])
        
        if boiler_enabled != 1:
            checkInterval = checkInterval * 2
        if _platform == "linux" or _platform == "linux2":
            self.logger.info("checking heat levels")
            buttonCheckHeat("main")
            self.logger.info("starting heartbeat")
            hBeat(checkInterval)
            self.logger.info("Memory free this loop %s MB" % hardware.getRAM())
            self.logger.info("CPU Usage this loop %s" % hardware.getCPUUse())
            self.logger.debug( "loop interval : %s" %(checkInterval))
            self.doLoop()
        else:
            from max import checkHeat
            checkHeat()
            threading.Timer(checkInterval, self.doLoop).start()
            self.logger.info('Running Windows timer')
    
    def startKioskServer(self):
        webIP, webPort = Variables().readVariables(['WebIP', 'WebPort'])
        self.logger.info("Web UI Starting on : %s %s" %( webIP, webPort))
        try:
            s_server = ThreadingHTTPServer((webIP, webPort), MyRequestHandler)
            uithread = threading.Thread(target=s_server.serve_forever)
            uithread.setDaemon(True)
            uithread.start()
        except Exception, err:
            self.logger.error("Unable to start Web Server on %s %s %s" %(webIP, webPort, err))
            self.logger.critical("Killing all Python processes so cron can restart")
            system("sudo pkill python")
        

if __name__=='__main__':
    Main()

        
    
