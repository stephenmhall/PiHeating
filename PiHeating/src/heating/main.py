#!/usr/bin/python
'''
Created on 1 Nov 2015

@author: stephen H

test change

'''
from __future__ import division

__updated__ = "2016-07-23"

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
import time
#from max import checkHeat, initialiseNeoPixel
from max import MaxInterface

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()

reboot_Timer = 0.0
offTime = 0.0
shutdown_Timer = 0.0
shutOff_Timer = 0.0


def mainCheckHeat(self):
    MaxInterface().checkHeat(input_queue)

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests is separate thread"""
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True,
                 queue=None):
        self.queue = queue
        HTTPServer.__init__(self, server_address, RequestHandlerClass,
                           bind_and_activate=bind_and_activate)
        
class Main():
    
    def __init__(self):
        #Initialise the Logger
        logLevel = Variables().readVariables(['LoggingLevel']).rstrip('\r')
        useNeoPixel = Variables().readVariables(['UseNeoPixel'])
        self.logger = logging.getLogger("main")
        level = logging.getLevelName(logLevel)
        self.logger.setLevel(level)
        
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
            self.arduino = neopixelserial.SerialProcess(input_queue, output_queue)
            self.arduino.daemon = True
            self.arduino.start()

        # Or start the GPIO
        else:
            setupGPIO()
        
        # Start Web UI
        self.startKioskServer()
        
        # Start Main Loop
        self.doLoop()
        
    def doLoop(self):
        nextLoopCheck = time.time()
        while True:
            loopStartTime = time.time()
            if loopStartTime >= nextLoopCheck:
                print "running loop"
                checkInterval, boiler_enabled, useNeoPixel = Variables().readVariables(['Interval', 'BoilerEnabled', 'UseNeoPixel'])
                
                if boiler_enabled != 1:
                    checkInterval = checkInterval * 2
                if _platform == "linux" or _platform == "linux2":
                    if not useNeoPixel:
                        self.logger.info("checking heat levels")
                        buttonCheckHeat("main")
                        self.logger.info("starting heartbeat")
                        hBeat(checkInterval)
                        self.logger.info("Memory free this loop %s MB" % hardware.getRAM())
                        self.logger.info("CPU Usage this loop %s" % hardware.getCPUUse())
                        self.logger.debug( "loop interval : %s" %(checkInterval))
                        self.doLoop()
                    else:
                        self.logger.info("checking heat levels")
                        MaxInterface().checkHeat(input_queue)
                        self.logger.info('Running NeoPixel timer')
                        self.logger.info("Memory free this loop %s MB" % hardware.getRAM())
                        self.logger.info("CPU Usage this loop %s" % hardware.getCPUUse())
                        self.logger.debug( "loop interval : %s" %(checkInterval))
                else:
                    MaxInterface().checkHeat()
                    self.logger.info('Running Windows timer')
                    
                
                    
                nextLoopCheck = loopStartTime + checkInterval
                
            if not output_queue.empty():
                serialData = output_queue.get().rstrip()
                self.processSerial(serialData)

            time.sleep(.2)
            
    
            
    def processSerial(self, data):
        global reboot_Timer
        global offTime
        global shutdown_Timer
        global shutOff_Timer
        
        self.logger.info("Processing Serial Data : %s" % data)
        if data == "checkSW_ON":
            MaxInterface().checkHeat(input_queue)
        elif data == "boilerSW_ON":
            boilerEnabled = Variables().readVariables(['BoilerEnabled'])
            if boilerEnabled:
                boilerEnabled = 0
            else:
                boilerEnabled = 1
            Variables().writeVariable([['BoilerEnabled', boilerEnabled]])
            MaxInterface().checkHeat(input_queue)
            
        elif data == "rebootSW_ON":
            reboot_Timer = time.time()
            MaxInterface().setNeoPixel(0, input_queue, 2)
        elif data == "rebootSW_OFF":
            offTime = time.time()
            if offTime - reboot_Timer >= 3:
                self.logger.info("Rebooting")
                system("sudo reboot")
                
        elif data == "shutdownSW_ON":
            shutdown_Timer = time.time()
            MaxInterface().setNeoPixel(0, input_queue, 1)
        elif data == "shutdownSW_OFF":
            shutOff_Timer = time.time()
            if shutOff_Timer - shutdown_Timer >= 3:
                self.logger.info("Shutting Down Python")
                system("sudo shutdown -h now")
                
        elif data == "overSW_ON":
            boiler_override = Variables().readVariables(['BoilerOverride'])
            boiler_override += 1
            if boiler_override > 2:
                boiler_override = 0
            print boiler_override
            Variables().writeVariable([['BoilerOverride', boiler_override]])
            MaxInterface().setNeoPixel(0, input_queue, 0)

            
            
    
    def startKioskServer(self):
        webIP, webPort = Variables().readVariables(['WebIP', 'WebPort'])
        self.logger.info("Web UI Starting on : %s %s" %( webIP, webPort))
        try:
            server = ThreadingHTTPServer((webIP, webPort), MyRequestHandler, queue=input_queue)
            uithread = threading.Thread(target=server.serve_forever)
            uithread.setDaemon(True)
            uithread.start()
        except Exception, err:
            self.logger.error("Unable to start Web Server on %s %s %s" %(webIP, webPort, err))
            self.logger.critical("Killing all Python processes so cron can restart")
            system("sudo pkill python")
        

if __name__=='__main__':
    Main()

        
    
