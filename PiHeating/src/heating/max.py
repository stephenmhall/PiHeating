
import logging
from database import DbUtils
from variables import Variables
from webui import CreateUIPage
#from heatinggpio import MyGpio
import base64
import socket
import datetime
import time
import sys
import urllib2
import json
import requests

maxDetails = {}
rooms = {}
devices = {}
valves = {}
valveList = []
message = ""
boilerOn = 0
weekDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
outsideTempCheck = 0

module_logger = logging.getLogger("main.max")

class Max():
    
    def checkHeat(self):
        MAXData, validData = self.getData()
        if validData:
            self.parseData(MAXData)
            self.switchHeat()
            
            
    def getData(self):
        self.logger = logging.getLogger("main.max.getData")
        validData = False
        message = ""
        Max_IP, Max_Port = Variables().readVariables(['MaxIP', 'MaxPort'])
        self.logger.info('Max Connection Starting on : %s %s ' % (Max_IP, Max_Port))
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            self.logger.info('Socket Created')
        except socket.error:
            self.logger.exception("unable to create socket")
            s.close()
            sys.exit()
             
        #Connect to remote server
        try:
            s.connect((Max_IP, int(Max_Port)))
            self.logger.info('Socket Connected to Max on ip %s' % Max_IP)
        except Exception, err:
            s.close()
            Variables().writeVariable([['CubeOK', 0]])
            self.logger.exception("unable to make connection, trying later %s" % err)
            CreateUIPage().updateWebUI()
            return (message, validData)
         
        try:
            while 1:
                reply = s.recv(1024)
                message += reply
        except:
            self.logger.info("Message ended")
            
        if message != "":
            Variables().writeVariable([['CubeOK', 1]])
            validData = True
            
        s.close()
        self.logger.debug(message)
        return (message, validData) 
    
    def parseData(self, message):
        print_on = int(Variables().readVariables(['PrintData']))
        message = message.split('\r\n')
    
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
        DbUtils().updateCube(msg)
        
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
        DbUtils().updateRooms(dbMessage)
        dbMessage = []
        for keys in devices:
            dbList = keys,devices[keys][0],devices[keys][1],devices[keys][2],devices[keys][3],devices[keys][5]
            dbMessage.append(dbList)
        DbUtils().updateDevices(dbMessage)
                
    def maxCmd_L(self, line):
        """ process L response """
        line = line.split(":")
        #print line
        es = base64.b64decode(line[1])
        #print es
        es_pos = 0
        
        while (es_pos < len(es)):
            dev_len = ord(es[es_pos]) + 1
            valve_adr = self.hexify(es[es_pos + 1:es_pos + 4])
            valve_status = ord(es[es_pos + 0x05])
            valve_info = ord(es[es_pos + 0x06])
            valve_temp = 0xFF
            valve_curtemp = 0xFF

            valve_info_string = '{0}{{:{1}>{2}}}'.format('ob', 0, 8).format(bin(valve_info)[2:])
            valve_mode = str(valve_info_string[8:])

            if valve_mode == '00':
                valve_MODE = 'AUTO'
            elif valve_mode == '01':
                valve_MODE = 'MANUAL'
            elif valve_mode == '11':
                valve_MODE = 'BOOST'
            elif valve_mode == '10':
                valve_MODE = 'VACATION'
            
            link_status = int(valve_info_string[3:4])
            battery_status = int(valve_info_string[2:3])
            
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
            
            valves.update({valve_adr: [valve_pos, valve_temp, valve_curtemp, valve_MODE, link_status, battery_status]})
            # save status and info
            #devices[valve_adr][6] = valve_status
            #devices[valve_adr][7] = valve_info
            es_pos += dev_len
            
        dbMessage = []
        for keys in valves:
            dbList = keys,valves[keys][0],valves[keys][1],valves[keys][2],valves[keys][3],valves[keys][4],valves[keys][5]
            dbMessage.append(dbList)
        DbUtils().updateValves(dbMessage)
            

        
    def getCurrentOutsidetemp(self):
        """
        Get Current outside temperature from OpenWeatherMap using the API
        """
        self.logger = logging.getLogger("main.max.getCurrentOutsidetemp")
        try:
            cityID, userKey = Variables().readVariables(['WeatherCityID', 'WeatherKey'])
            f = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?id={}&APPID={}'.format(cityID,userKey))
            json_string = f.read()
            parsed_json = json.loads(json_string)
            temp_k = parsed_json['main']['temp'] # kelvin -273.15
            temp_c = temp_k - 273.15
            f.close()
            self.logger.info("Outside temp is %sK %sC" % (temp_k,temp_c))
            return temp_c
        except Exception, err:
            self.logger.exception("No temp data %s" % err)
        
    def switchHeat(self):
        logTime = time.time()
        boilerEnabled, veraControl, Vera_Address, Vera_Port, \
        Vera_Device, singleRadThreshold, multiRadThreshold, \
        multiRadCount, AllValveTotal = Variables().readVariables(['BoilerEnabled', 
                                           'VeraControl', 
                                           'VeraIP', 
                                           'VeraPort', 
                                           'VeraDevice',
                                           'SingleRadThreshold',
                                           'MultiRadThreshold',
                                           'MultiRadCount',
                                           'AllValveTotal'])
        
        roomTemps = CreateUIPage().createRooms()
        outsideTemp = self.getCurrentOutsidetemp()
        
        for i in range (len(roomTemps)):
            roomTemps[i] = roomTemps[i] + (str(outsideTemp),)

        # Calculate if heat is required
        valveList = []
        for room in roomTemps:
            valveList.append(room[4])

        singleRadOn = sum(i >= singleRadThreshold for i in valveList)
        multiRadOn  = sum(i >= multiRadThreshold for i in valveList)
        totalRadOn  = sum(valveList)
        
        if singleRadOn >= 1 or multiRadOn >= multiRadCount or totalRadOn >= AllValveTotal:
            boilerState = 1
        else:
            boilerState = 0
        print 'Boiler is ', boilerEnabled
        print 'Heating is ', boilerState
        
        # Update Temps database
        DbUtils().insertTemps(roomTemps)

        if boilerEnabled:
            try:
                _ = requests.get(veraControl.format(Vera_Address, Vera_Port, 
                                                    Vera_Device, str(boilerState)), timeout=5)
                Variables().writeVariable([['VeraOK', 1]])
                print 'message sent to Vera'
            except:
                Variables().writeVariable([['VeraOK', 0]])
                print "vera is unreachable"
        else:
            boilerState = 0
            try:
                _ = requests.get(veraControl.format(Vera_Address, Vera_Port, 
                                                    Vera_Device, boilerState), timeout=5)
                Variables().writeVariable([['VeraOK', 1]])
                print "Boiler is Disabled"
            except:
                Variables().writeVariable([['VeraOK', 0]])
                print "vera is unreachable"
        try:
            boilerOn = DbUtils().getBoiler()[2]
        except:
            boilerOn = 9
            
        if boilerState != boilerOn:
            msg = (logTime,boilerState)
            DbUtils().updateBoiler(msg)
        boilerOn = boilerState

        # Create UI Pages
        CreateUIPage().saveUI(roomTemps)
        CreateUIPage().saveAdminUI()