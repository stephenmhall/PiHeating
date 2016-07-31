'''
Created on 31 Jul 2016

@author: steph
'''
import requests
from variables import Variables

class VeraVirtualTemps(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.veraSendCommand, self.veraIP, self.veraPort = Variables().readVariables(['VeraUpdateTemps', 'VeraIP', 'VeraPort'])
        
    def veraSendTemp(self, roomID, temp):
        try:
            _ = requests.get(self.veraSendCommand.format(self.veraIP, self.veraPort, 
                                                    roomID, str(temp)), timeout=5)
        except:
            pass
        