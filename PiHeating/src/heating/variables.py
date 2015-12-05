'''
Created on 3 Dec 2015

@author: steph
'''

class Variables(object):

        
    def readVariables(self, variableName):
        data = self.variableData()
        if variableName == 'ALL':
            return data
        for lines in data:
            line = lines.split('=')
            if line[0] == variableName:
                return line[1]
                
    def writeVariable(self, variableName, variableData):
        data = self.variableData()
        print 'data : ', data
        for i in range(len(data)):
            if data[i].split('=')[0] == variableName:
                data[i] = "{}={}".format(variableName,variableData)
                break
        with open('variables.txt', 'w') as f:
            for items in data:
                print>>f, items
                
    def variableData(self):
        with open('variables.txt', 'r') as f:
            data = f.read().split('\n')
        return data
                
                
                
            