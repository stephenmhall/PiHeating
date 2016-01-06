'''
Created on 6 Dec 2015

@author: steph
'''

#import requests
import logging
import binascii
import socket
import sys
import time
#import base64
from variables import Variables
from database import DbUtils
from webui import CreateUIPage

VAR = Variables()

class SendMessage(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.baseString = "000440000000"
        
        
        
    def s_Command(self, rfAddress, roomID, thermostatMode, setpointTemperature):
        """
        Base String        6           000440000000
        RF Address         3           0FDAED
        Room nr            1           01
        Temperature  &     1           66
        Mode (similar to the L message)
        Date Until         1           04  Note: Only in case of vacation mode setting. Otherwise this byte is omitted
        
        hex:  |    66     |
        dual: | 0110 1100 |
                |||| ||||
                ||++-++++-- temperature: 10 1100 -> 38 = temp * 2
                ||                     (to get the temperature, the value must be divided by 2: 38/2 = 19)
                ||
                ||
                ++--------- mode: 00=auto/weekly program
                            01=manual
                            10=vacation
                            11=boost
        """
        self.logger = logging.getLogger("main.sendmessage.s_Command")
        self.logger.info("creating s command for %s %s %s %s" %(rfAddress, roomID, thermostatMode, setpointTemperature))
        self.rfAddress = rfAddress
        self.roomID = format(int(roomID), '02x')        
        self.setpointTemperature = int(float(setpointTemperature) * 2)
        bits = '{0:06b}'.format(self.setpointTemperature)
        self.logger.debug("setpoint temp in bits : %s" % bits)
        
        if thermostatMode != 'none':
            if thermostatMode == 'MANUAL':
                bits = '01' + bits
            elif thermostatMode == 'BOOST':
                bits = '11' + bits
            elif thermostatMode == 'VACATION':
                bits = '10' + bits
            else:
                bits = '00' + bits
        
        self.logger.debug("bits with mode added : %s" % bits)
        bits = hex(int(bits, 2))[2:]
        self.logger.debug("temp bits as Hex : %s" % bits)
        if bits == '0':
            bits = '00'
            
        if thermostatMode == 'none':
            commandString = self.baseString + self.rfAddress + self.roomID
        else:
            commandString = self.baseString + self.rfAddress + self.roomID + bits
            
        self.logger.debug("command string : %s" % commandString)
        commandString = self.hextoBase64(commandString)
        self.logger.debug("Encoded string : %s" % commandString)
        return commandString
    
    def hextoBase64(self, hexnumber):
        hexified = hexnumber.decode("hex")
        base = binascii.b2a_base64(hexified)
        return base
    
    #Auto AARAAAAAEFHaAwA= 00 04 40 00 00 00  10 51 da  03 00
    #manu AARAAAAAEFHWBAA= 00 04 40 00 00 00  10 51 d6  04 00
    #     AARAAAAAEWtjAgA= 00 04 40 00 00 00  11 6b 63  02 00
    #     AARAAAAAEWOlAWY= 00 04 40 00 00 00  11 63 A5  01 66
    #('1163A5', 1, 'MANUAL', 19) 
    
    
    def sendMAX(self, commandString):
        self.logger = logging.getLogger("main.sendmessage.sendMAX")
        sendString = 's:{}\r\n'.format(commandString)
        Max_IP, Max_Port = VAR.readVariables(['MaxIP', 'MaxPort'])
        self.logger.info("Sending s command to MAX on : %s %s" % (Max_IP, Max_Port))
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            self.logger.debug("Max Socket Created")
        except socket.error:
            self.logger.exception("Failed to create MAX socket")
            s.close()
            sys.exit()
             
        #Connect to remote server
        try:
            s.connect((Max_IP, int(Max_Port)))
            self.logger.debug("Connected to Max on ip %s" % Max_IP)
        except Exception, err:
            s.close()
            self.logger.exception("Unable to make MAX connection Trying later %s" % err)
            return
         
        
        message = ""
        try:
            while 1:
                reply = s.recv(1024)
                message += reply
        except:
            pass
            
        if message != "":
            validData = True
            self.logger.info("Sending message to MAX : %s" % sendString)
            s.send(sendString)
            message = ""
            try:
                while 1:
                    reply = s.recv(1024)
                    message += reply
            except:
                pass
            
        s.close()
        self.logger.debug("MAX send message reply %s" % message)
        return message
    
    
    def updateRoom(self, roomData):
        self.logger = logging.getLogger("main.sendmessage.updateRoom")
        self.logger.info("Updating rooms")
        roomList = DbUtils().getRooms()
        self.logger.debug("roomList %s" % roomList)
        self.logger.debug("roomData %s" % roomData)
        roomSplit = roomData.split('?')
        mode = roomSplit[1].replace('%20', ' ')
        room = roomSplit[2].replace('%20', ' ')
        temp = roomSplit[3].replace('%20', ' ')
        self.logger.debug("room %s mode %s temp %s" % (room, mode, temp))
        
        if mode == 'eco':
            for rooms in roomList:
                sCommand = self.s_Command(rooms[2], rooms[0], 'none', 0.0)
                self.logger.debug("eco sCommand %s" % sCommand)
                self.sendMAX(sCommand)
                time.sleep(0.8)
                
        if mode == 'ECO':
            for rooms in roomList:
                if room == rooms[1]:
                    sCommand = self.s_Command(rooms[2], rooms[0], 'none', 0.0)
                    self.logger.debug("ECO sCommand %s" % sCommand)
                    self.sendMAX(sCommand)
                
        elif mode == 'auto':
            for rooms in roomList:
                sCommand = self.s_Command(rooms[2], rooms[0], 'AUTO', 0.0)
                self.logger.debug("auto sCommand %s" % sCommand)
                self.sendMAX(sCommand)
                time.sleep(0.8)
        
        else:
            # For standard room change
            for rooms in roomList:
                if room == rooms[1]:
                    sCommand = self.s_Command(rooms[2], rooms[0], mode, temp)# rf address,room Number, mode, temp
                    self.logger.debug("standard sCommand %s" % sCommand)
                    self.sendMAX(sCommand)
                
        CreateUIPage().updateWebUI()
                
        