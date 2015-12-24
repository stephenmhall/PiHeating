#!/usr/bin/python
'''
Created on 1 Nov 2015

@author: stephen H

test change

'''
from __future__ import division

__updated__ = "2015-12-22"

import threading
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from requesthandler import MyRequestHandler
from heatinggpio import MyGpio
from database import DbUtils
from variables import Variables
from max import Max
from sys import platform as _platform



class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests is separate thread"""
    
    
class Main():
    
    def __init__(self):
        try:
            DbUtils().getCubes()
        except:
            DbUtils().initialiseDB()

        self.startKioskServer()
        self.doLoop()
        
               
            
    def doLoop(self):
        checkInterval, boiler_enabled = Variables().readVariables(['Interval', 'BoilerEnabled'])
        Max().checkHeat()
        if boiler_enabled != 1:
            checkInterval = checkInterval * 2
        if _platform == "linux" or _platform == "linux2":
            MyGpio().heartbeat(checkInterval)
            #print 'loop interval : ',checkInterval
            self.doLoop()
        else:
            threading.Timer(checkInterval, self.doLoop).start()
    
    def startKioskServer(self):        
        webIP, webPort = Variables().readVariables(['WebIP', 'WebPort'])
        print 'Web UI Starting on : ', webIP, webPort
        s_server = ThreadingHTTPServer((webIP, webPort), MyRequestHandler)
        uithread = threading.Thread(target=s_server.serve_forever)
        uithread.setDaemon(True)
        uithread.start()
        

if __name__=='__main__':
    Main()

        
    
