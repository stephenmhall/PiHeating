#!/usr/bin/python
'''
Created on 1 Nov 2015

@author: stephen H

test change

'''



from __future__ import division

__updated__ = "2015-12-01"


import socket   #for sockets
import sys  #for exit
import base64
import datetime
import time
import requests
import threading
import urllib2
import json

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

from heating.requesthandler import MyRequestHandler
from database import DbUtils
from heating.webui import CreateUIPage
CUI = CreateUIPage()
DB = DbUtils()

maxDetails = {}
rooms = {}
devices = {}
valves = {}
valveList = []
message = ""
validData = False
veraControl = "{}/data_request?id=lu_action&output_format=xml&DeviceNum={}&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget&newTargetValue={}"
boilerOn = 0
weekDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']



class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests is separate thread"""

class MainWindow():
    def __init__(self):
        try:
            DB.getVariables()
        except:
            DB.initialiseDB()

        self.startKioskServer()
        self.doLoop()
        self.outsideTempCheck = 0
        self.outsideTemp = self.getCurrentOutsidetemp()
        
    def onBoilerSwitch(self):
        try:
            isBoilerON = int(DB.getVariables()[5])
        except:
            isBoilerON = 0
        if isBoilerON:
            isBoilerON = 0
        else:
            isBoilerON = 1
        DB.updateBoilerState(isBoilerON)
        self.switchHeat()
    
    def OnUpdateTime(self):
        self.nowTime = time.strftime("%b %d %Y %H:%M:%S", time.localtime(time.time()))
        self.timeString.set(self.nowTime)
        
    def hexify(self, tmpadr):
        """ returns hexified address """
        return "".join("%02x" % ord(c) for c in tmpadr).upper()
        
    def maxCmd_H(self, line):
        """ process H response """
        line = line.split(',')
        serialNumber = line[0][2:]
        rfChannel = line[1]
        maxId = line[2]
        dutyCycle = int(line[5], 16)
        maxDetails['serialNumber'] = serialNumber
        maxDetails['rfChannel'] = rfChannel
        maxDetails['maxId'] = maxId
        
        msg = (maxId,serialNumber,rfChannel,dutyCycle)
        DB.updateCube(msg)
        
    def maxCmd_C(self, line):
        """ process C response """
        line = line.split(",")
        es = base64.b64decode(line[1])
        if ord(es[0x04]) == 1:
            dev_adr = self.hexify(es[0x01:0x04])
            devices[dev_adr][8] = es[0x16]
        
    def maxCmd_M(self, line, refresh):
        """ process M response Rooms and Devices"""
        line = line.split(",")
        es = base64.b64decode(line[2])
        room_num = ord(es[2])
        es_pos = 3
        this_now = datetime.datetime.now()
        for _ in range(0, room_num):
            room_id = str(ord(es[es_pos]))
            room_len = ord(es[es_pos + 1])
            es_pos += 2
            room_name = es[es_pos:es_pos + room_len]
            es_pos += room_len
            room_adr = es[es_pos:es_pos + 3]
            es_pos += 3
            if room_id not in rooms or refresh:
                #                     id   :0room_name, 1room_address,   2is_win_open
                rooms.update({room_id: [room_name, self.hexify(room_adr), False]})
        dev_num = ord(es[es_pos])
        es_pos += 1
        for _ in range(0, dev_num):
            dev_type = ord(es[es_pos])
            es_pos += 1
            dev_adr = self.hexify(es[es_pos:es_pos + 3])
            es_pos += 3
            dev_sn = es[es_pos:es_pos + 10]
            es_pos += 10
            dev_len = ord(es[es_pos])
            es_pos += 1
            dev_name = es[es_pos:es_pos + dev_len]
            es_pos += dev_len
            dev_room = ord(es[es_pos])
            es_pos += 1
            if dev_adr not in devices or refresh:
                #                            0type     1serial 2name     3room    4OW,5OW_time, 6status, 7info, 8temp offset
                devices.update({dev_adr: [dev_type, dev_sn, dev_name, dev_room, 0, this_now, 0, 0, 7]})
        dbMessage = []
        for keys in rooms:
            dbList = keys,rooms[keys][0],rooms[keys][1]
            dbMessage.append(dbList)
        DB.updateRooms(dbMessage)
        dbMessage = []
        for keys in devices:
            dbList = keys,devices[keys][0],devices[keys][1],devices[keys][2],devices[keys][3],devices[keys][5]
            dbMessage.append(dbList)
        DB.updateDevices(dbMessage)
                
    def maxCmd_L(self, line):
        """ process L response """
        line = line.split(":")
        es = base64.b64decode(line[1])
        es_pos = 0
        while (es_pos < len(es)):
            dev_len = ord(es[es_pos]) + 1
            valve_adr = self.hexify(es[es_pos + 1:es_pos + 4])
            valve_status = ord(es[es_pos + 0x05])
            valve_info = ord(es[es_pos + 0x06])
            valve_temp = 0xFF
            valve_curtemp = 0xFF
            # WallMountedThermostat (dev_type 3)
            if dev_len == 13:
                valve_pos = 999
                if valve_info & 3 != 2:
                    valve_temp = float(int(self.hexify(es[es_pos + 0x08]), 16)) / 2  # set temp
                    valve_curtemp = float(int(self.hexify(es[es_pos + 0x0C]), 16)) / 10  # measured temp
            # HeatingThermostat (dev_type 1 or 2)
            elif dev_len == 12:
                valve_pos = ord(es[es_pos + 0x07])
                if valve_info & 3 != 2:
                    valve_temp = float(int(self.hexify(es[es_pos + 0x08]), 16)) / 2
                    valve_curtemp = float(ord(es[es_pos + 0x0A])) / 10
            
            # WindowContact
            elif dev_len == 7:
                pass
            
            valves.update({valve_adr: [valve_pos, valve_temp, valve_curtemp]})
            # save status and info
            devices[valve_adr][6] = valve_status
            devices[valve_adr][7] = valve_info
            es_pos += dev_len
        dbMessage = []
        for keys in valves:
            dbList = keys,valves[keys][0],valves[keys][1],valves[keys][2]
            dbMessage.append(dbList)
        DB.updateValves(dbMessage)
            
    def getData(self):
        global validData
        Max_Variables = DB.getVariables()
        Max_IP = Max_Variables[1]
        Max_Port = Max_Variables[2]
        print Max_IP, Max_Port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            print 'Socket Created'
        except socket.error:
            print 'Failed to create socket'
            s.close()
            sys.exit()
             
        #Connect to remote server
        try:
            s.connect((Max_IP , Max_Port))
            print 'Socket Connected to Max on ip ' + Max_IP
        except:
            s.close()
            DB.updateCubeState(0)
            #CUI.saveUI()
            #CUI.saveAdminUI()
            print "Unable to make connection Trying later"
            return
         
        
        message = ""
        try:
            while 1:
                reply = s.recv(1024)
                #print reply
                message += reply
        except:
            print "Message ended"
            
        if message != "":
            DB.updateCubeState(1)
            validData = True
            
        s.close()
        return message        
    
    def parseData(self, message):
        Vera_Variables = DB.getVariables()
        print_on = int(Vera_Variables[7])
        message = message.split('\r\n')
        global validData
    
        for lines in message:
            #print lines
            try:
                if lines[0] == 'H':
                    self.maxCmd_H(lines)
                elif lines[0] == 'M':
                    self.maxCmd_M(lines, 0)
                elif lines[0] == 'C':
                    self.maxCmd_C(lines)
                elif lines[0] == 'L':
                    self.maxCmd_L(lines)
                else:
                    break
            except:
                pass
    
        if print_on:
            for keys in maxDetails:
                print keys, maxDetails[keys]
            print "Rooms"
            for keys in rooms:
                print keys, rooms[keys]
            print "devices"
            for keys in devices:
                print keys, devices[keys]
            print "valves"
            for keys in valves:
                print keys, valves[keys]
        validData = False
        
    def getCurrentOutsidetemp(self):
        try:
            f = urllib2.urlopen('http://api.wunderground.com/api/0401dc3c2aa3313a/conditions/q/57.155689,-2.295520.json')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            #location = parsed_json['location']['city']
            temp_c = parsed_json['current_observation']['temp_c']
            #print "Current temperature is: %s" % ( temp_c)
            f.close()
            return temp_c
        except:
            print "no temp"
        
    def switchHeat(self):
        logTime = time.time()
        Vera_Variables = DB.getVariables()
        boilerEnabled = int(Vera_Variables[5])
        Vera_Address = Vera_Variables[3]
        Vera_Device = Vera_Variables[4]
        
        roomTemps = CUI.createRooms()
        
        if self.outsideTempCheck == 3:
            self.outsideTemp = self.getCurrentOutsidetemp()
            self.outsideTempCheck = 0
        else:
            self.outsideTempCheck += 1
        
        for i in range (len(roomTemps)):
            roomTemps[i] = roomTemps[i] + (str(self.outsideTemp),)

        # Calculate if heat is required
        valveList = []
        for room in roomTemps:
            valveList.append(room[4])

        singleRadOn = sum(i >= 80 for i in valveList)
        multiradOn  = sum(i >= 60 for i in valveList)
        
        if singleRadOn >= 1 or multiradOn >= 2:
            boilerState = 1
        else:
            boilerState = 0
        print 'Boiler is ', boilerEnabled
        print 'Heating is ', boilerState
        
        # Update Temps database
        DB.insertTemps(roomTemps)

        if boilerEnabled:
            try:
                _ = requests.get(veraControl.format(Vera_Address, Vera_Device, str(boilerState)), timeout=5)
                DB.updateVeraState(1)
                print 'message sent to Vera'
            except:
                DB.updateVeraState(0)
                print "vera is unreachable"
        else:
            boilerState = 0
            try:
                _ = requests.get(veraControl.format(Vera_Address, Vera_Device, boilerState), timeout=5)
                DB.updateVeraState(1)
                print "Boiler is Disabled"
            except:
                DB.updateVeraState(0)
                print "vera is unreachable"
        try:
            boilerOn = DB.getBoiler()[2]
        except:
            boilerOn = 9
            
        # Create UI Pages
        CUI.saveUI(roomTemps)
        CUI.saveAdminUI()

        if boilerState != boilerOn:
            msg = (logTime,boilerState)
            #print 'switch heat DB message ', msg
            DB.updateBoiler(msg)
        boilerOn = boilerState
            
        
    def doLoop(self):
        checkInterval = DB.getVariables()[6]
        boiler_enabled = DB.getVariables()[5]
        MAXData = self.getData()
        if validData:
            self.parseData(MAXData)
            self.switchHeat()
        if boiler_enabled != 1:
            checkInterval = checkInterval * 2
        threading.Timer(checkInterval, self.doLoop).start()
    
    
        
    def startKioskServer(self):
        variables = DB.getVariables()
        webIP = variables[8]
        webPort = variables[9]
        
        s_server = ThreadingHTTPServer((webIP, webPort), MyRequestHandler)
        uithread = threading.Thread(target=s_server.serve_forever)
        uithread.setDaemon(True)
        uithread.start()
        
        
    def closeWindow(self):
        self.parent.destroy()

if __name__=='__main__':
    MainWindow()

        
    
