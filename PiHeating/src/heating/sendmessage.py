'''
Created on 6 Dec 2015

@author: steph
'''

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
        self.rfAddress = rfAddress
        self.roomID = str(hex(roomID)[2:])
        self.setpointTemperature = int(setpointTemperature) * 2
        bits = '{0:08b}'.format(self.setpointTemperature)
        
        if thermostatMode == 'MANUAL':
            bits += '01'
        elif thermostatMode == 'BOOST':
            bits += '11'
        else:
            bits += '00'
            
        bits = str(hex(int(bits))[2:])
            
        commandString = self.baseString + self.rfAddress + self.roomID + bits
        return commandString