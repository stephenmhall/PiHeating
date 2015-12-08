'''
Created on 6 Dec 2015

@author: steph
'''

import requests
import socket
import sys
import base64
from variables import Variables
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
        self.rfAddress = rfAddress
        self.roomID = format(roomID, '02x')
        print 'room ID : ', self.roomID
        self.setpointTemperature = int(setpointTemperature) * 2
        bits = '{0:06b}'.format(self.setpointTemperature)
        print 'setpoint temp in bits : ', bits
        
        if thermostatMode == 'MANUAL':
            bits = '01' + bits
        elif thermostatMode == 'BOOST':
            bits = '11' + bits
        else:
            bits = '00' + bits
        
        print 'bits with mode added : ', bits
            
        bits = hex(int(bits, 2))[2:]
        print 'temp bits as Hex : ', bits
            
        commandString = self.baseString + self.rfAddress + self.roomID + bits
        print 'command string : ', commandString
        commandString = base64.b64encode(commandString)
        print 'encoded string : ', commandString
        return commandString
    
    def sendMAX(self, commandString):
        sendString = 's:{}'.format(commandString)
#         maxIP, maxPort = VAR.readVariables(['MaxIP', 'MaxPort'])
#         print 'sending s command to Max : ', sendString
#         try:
#             r = requests.get(sendString, timeout=5)
#             print r.text
#         except:
#             pass
        Max_IP, Max_Port = VAR.readVariables(['MaxIP', 'MaxPort'])
        print 'Max Connection Starting on : ',Max_IP, Max_Port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            print 'Socket Created'
        except socket.error:
            print 'Failed to create Send socket'
            s.close()
            sys.exit()
             
        #Connect to remote server
        try:
            s.connect((Max_IP, int(Max_Port)))
            print 'Socket Connected to Max on ip ' + Max_IP
        except:
            s.close()
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
            
        #print 'connect message : ', message
            
        if message != "":
            validData = True
            s.send(sendString)
            message = ""
            try:
                while 1:
                    reply = s.recv(1024)
                    #print reply
                    message += reply
            except:
                pass
            
        s.close()
        #print 'S Message : ', message
        return message        