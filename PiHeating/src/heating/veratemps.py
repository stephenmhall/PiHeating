'''
Created on 31 Jul 2016

@author: steph
'''
import requests
import ast
import logging
from variables import Variables

module_logger = logging.getLogger("main.veratemps")

class VeraVirtualTemps(object):
    '''
    classdocs
    '''
        
        
    def veraSendTemp(self, roomID, temp):
        logger = logging.getLogger("main.veratemps")
        
        veraSendCommand = Variables().readVariables(['VeraUpdateTemps'])
        try:
            sendString = veraSendCommand.format(roomID, temp)
            logger.info("Sending to Vera {}".format (sendString))
            _ = requests.get(sendString, timeout=5)
        except Exception, err:
            logger.info("vera send fault{}".format (err))
        
    def veraRoomDict(self, roomString):
        newString = roomString.replace(";", ",")
        roomDict = ast.literal_eval(newString)
        return roomDict
    
        