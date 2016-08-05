'''
Created on 23 Nov 2015

@author: steph
'''
import datetime
import time
import logging
import urllib
from database import DbUtils
DB = DbUtils()


class MakeGraph():
    def __init__(self):
        #self.createGraph()
        pass

    def createGraph(self, roomName):
        roomSplit = roomName.split('?')
        #cleanName = roomSplit[1].replace('%20', ' ')
        cleanName = urllib.unquote(roomSplit[1])
        graphPeriod = int(roomSplit[2])
        currentTime = time.time() - 86400 * graphPeriod
        tempData = DB.getTemps(cleanName, currentTime)
        boilerData = DB.getAllBoiler()
        pageText = []
        
        pageText.append(self.html_Top())
        pageText.append(self.html_Data(tempData, boilerData))
        pageText.append(self.html_Options(cleanName, (86400 * graphPeriod)))
        pageText.append(self.html_Chart())
        pageText.append(self.html_Body())
        
        html_text = "".join(pageText)# changed for ' in room name
        
        f = open('graph.html', 'w')
        f.write(html_text)
        f.close()
        
    def dutyCycle(self, interval):
        logger = logging.getLogger("main.graphing.dutycycle")
        logger.info("Calculating duty cycle for {} seconds".format(interval))
        currentTime = int(time.time())
        timeLimit = int(currentTime - interval) # 86400
        boilerStates = DB.getTimedBoiler(timeLimit)
        onTime = 0
        offTime = 0
        
        checkTime = timeLimit
        try:
            
            for times in boilerStates:
                loopTime = int(float(times[1]))
                loopState = times[2]
                elapsedTime = (loopTime - checkTime)
                if loopState:
                    offTime += elapsedTime
                else:
                    onTime += elapsedTime
                checkTime = loopTime
                
            elapsedTime = currentTime - checkTime
            
            if loopState:
                onTime += elapsedTime
            else:
                offTime += elapsedTime
                
            dutyCycle = 100 / (interval / onTime)
            
        except Exception, err:
            logger.info('No duty cycle data because {}'.format(err))
            dutyCycle = 0
            
        logger.info("Duty Cycle :{}%".format(dutyCycle)) 
        return int(dutyCycle)
        


    def html_Top(self):
        html_text = """<html>
            <head>
                <script type="text/javascript" src="https://www.google.com/jsapi"></script>
                <script type="text/javascript">
                    google.load("visualization", "1", {packages:["corechart"]});
                    google.setOnLoadCallback(drawVisualization);
                    """
        return html_text

    def html_Data(self, tempData, boilerData):
        pageText = []
        pageText.append("""function drawVisualization() {
            // Some raw data (not necessarily accurate)
            var data = google.visualization.arrayToDataTable([
                ['Time', 'SetPoint', 'Temperature', 'Outside Temp', 'Boiler',  'Valve %'],
                """)
        lastTemp = 0.0
        for lines in tempData:
            tempTime = lines[2]
            setPoint = lines[3]
            realTemp = float(lines[4])
            valvePos = lines[5] / 10.0
            outsideTemp = lines[7]
            
            try:
                outsideTemp = float(outsideTemp)
            except:
                outsideTemp = 0.0
                #print 'Not a float'

            # Exclude Zero Temperature values
            if realTemp > 0.0:
                lastTemp = realTemp
            if realTemp == 0.0 and lastTemp > 1.0:
                realTemp = 'null'
                
            # Find if boiler is on at temperature time
            for states in reversed(boilerData):
                if tempTime >= states[1]:
                    boilerOn = states[2] * 12
                    break
                
            timeString = (datetime.datetime.fromtimestamp(float(tempTime)).strftime('%d %H:%M'))
            pageText.append("""['{0}', {1}, {2}, {3:.1f}, {4}, {5}],
            """.format(timeString,setPoint,realTemp,outsideTemp,boilerOn,valvePos))
        pageText.append("""]);
        """)
        html_text = "".join(pageText)
        return html_text

    def html_Options(self, roomName, timeInterval):
        dutyCycle = self.dutyCycle(timeInterval)
        html_text = """
        var options = {{
            title : "Temperature of {}, Heating has been on {}% of the time",
            seriesType: 'line',
            interpolateNulls: true,
            series: {{
                2: {{curveType: 'function'}},
                3: {{type: 'area'}},
                4: {{type: 'area'}}
            }}
        }};
             """.format(roomName, dutyCycle)# Changed to double quote above
        return html_text

    def html_Chart(self):
        html_text = """
        var chart = new google.visualization.ComboChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }
        </script>
    </head>
            """
        return html_text

    def html_Body(self):
        html_text = """
            <body>
                <div id="chart_div" style="width: 100%; height: 600px;"></div>
                <a href="/index.html"><button type="button">Main UI</button></a>
            </body>
        </html>
            """
        return html_text
