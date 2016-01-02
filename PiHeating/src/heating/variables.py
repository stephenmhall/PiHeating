'''
Created on 3 Dec 2015

@author: steph
'''
import logging

class Variables(object):
    """
    Reads and writes the variables.txt file.
    Keys and variables separated by a comma
    """
        
    def readVariables(self, variableName):
        """
        Accepts list of Variable names and returns list of variable data
        or complete list if 'ALL' received
        """
        self.logger = logging.getLogger("main.variables.readVariables")
        
        data = self.variableData()
        if variableName == 'ALL':
            return data
        output = []
        for variable in variableName:
            self.logger.debug("reading %s" % variable)
            for lines in data:
                line = lines.split(',')
                if line[0] == variable:
                    try:
                        output.append(int(line[1]))
                    except:
                        output.append(str(line[1]))
        if len(output) == 1:
            output = output[0]
        return output
                    
    def writeVariable(self, variables):
        """
        Accepts List of Variable lists to change
        """
        self.logger = logging.getLogger("main.variables.writeVariables")
        self.logger.info("writing variables")
        data = self.variableData()
        for change in variables:
            for i in range(len(data)):
                if data[i].split(',')[0] == change[0]:
                    data[i] = "{},{}".format(change[0],change[1])
        #print data
        with open('variables.txt', 'w') as f:
            for items in data:
                if ',' in items:
                    self.logger.debug("Writing %s" % items)
                    print>>f, items
                
    def variableData(self):
        with open('variables.txt', 'r') as f:
            data = f.read().split('\n')
        return data