import time

from database import DbUtils
from variables import Variables

DB = DbUtils()
VAR = Variables()

class CreateUIPage():
    def __init__(self):
        """
        Create UI Webpage
        """
        
    def updateWebUI(self):
        roomTemps = self.createRooms()
        self.saveUI(roomTemps)
        self.saveAdminUI()
        
    def saveUI(self, roomTemps):
        #print 'SAVE UI'
        self.dutyCycle()
        pageTop = self.pageTop()
        pageHeaderMain = self.pageHeader('Main UI')
        pageHeaderAdmin = self.pageHeader('Admin')
        buttonLayout = self.buttonLayout()
        filler = self.filler()
        pageBottom = self.page_bottom()
        
        # Create main UI page
        pageText = []
        pageText.append(pageTop)
        pageText.append(pageHeaderMain)
        pageText.append(buttonLayout)
        pageText.append(self.roomTable(roomTemps))
        pageText.append(self.weatherWidget())
        pageText.append(filler)
        pageText.append(pageBottom)
        
        html_text = ''.join(pageText)
        
        indexFile = open('index.html', 'w')
        indexFile.write(html_text)
        indexFile.close()
        
        # Create Admin UI Page
        pageText = []
        pageText.append(pageTop)
        pageText.append(pageHeaderAdmin)
        pageText.append(buttonLayout)
        pageText.append(self.variablesPage())
        pageText.append(self.shutdownButton())
        pageText.append(filler)
        pageText.append(pageBottom)
        html_text = ''.join(pageText)

        indexFile = open('admin.html', 'w')
        indexFile.write(html_text)
        indexFile.close()
        
#     def saveAdminUI(self):
#         #print 'SAVE ADMIN UI'
#         pageText = []
#         pageText.append(self.pageTop())
#         pageText.append(self.pageHeader('Admin'))
#         pageText.append(self.buttonLayout())
#         pageText.append(self.variablesPage())
#         pageText.append(self.shutdownButton())
#         pageText.append(self.filler())
#         pageText.append(self.page_bottom())
#         html_text = ''.join(pageText)
# 
#         indexFile = open('admin.html', 'w')
#         indexFile.write(html_text)
#         indexFile.close()
        
    def rangeGraphUI(self):
        print 'Creating rangeGraph page'
        pageText = []
        pageText.append(self.pageTop())
        pageText.append(self.pageHeader())
        pageText.append(self.rangeGraphpage())
        pageText.append(self.buttonLayout())
        pageText.append(self.weatherWidget())
        pageText.append(self.homeButton())
        pageText.append(self.filler())
        pageText.append(self.page_bottom())
        html_text = ''.join(pageText)
        
        indexFile = open('rangegraph.html', 'w')
        indexFile.write(html_text)
        indexFile.close()
        
    def rangeGraphpage(self):
        #baseFontSize = float(VAR.readVariables(['BaseFontSize']))
        rooms = DB.getRooms()
        print rooms
        pageText = []
        pageText.append("""
            <div class="container-fluid bg-3">
                <div class="well well-sm">
                    <div class="btn-group">
                        <a class="btn dropdown-toggle btn-select" data-toggle="dropdown" href="#">Select a Room <span class="caret"></span></a>
                        <ul class="dropdown-menu">
                        """)
        # Add room dropdown
        for room in rooms:
            roomText = room[1]
            pageText.append("""<li><a href="#">{}</a></li>
            """.format(roomText))

        pageText.append("""
        </ul>
    </div>""")
                        
        pageText.append("""
        <div id="datetimepicker" class="input-append date">
      <input type="text"></input>
      <span class="add-on">
        <i data-time-icon="icon-time" data-date-icon="icon-calendar"></i>
      </span>
    </div>""")
        pageText.append("""
                </div>
            </div>    
            """)
        html_text = ''.join(pageText)
        return html_text
        
        
    def OnUpdateTime(self):
        self.nowTime = time.strftime("%b %d %Y %H:%M:%S", time.localtime(time.time()))
        return self.nowTime
    
    def dutyCycle(self):
        currentTime = time.time()
        timeLimit = currentTime - 86400
        boilerStates = DB.getTimedBoiler(timeLimit)
        try:
            startTime  = float(boilerStates[0][1])
            startState = boilerStates[0][2]
            
            timeBoilerOn  = 0
            timeBoilerOff = 0
            
            for i in range(1, len(boilerStates)):
                stateTime = float(boilerStates[i][1]) - startTime
                if startState == 1:
                    timeBoilerOn  += stateTime
                else:
                    timeBoilerOff += stateTime
                startTime  = float(boilerStates[i][1])
                startState = boilerStates[i][2]
            
            dutyCycle = 100 / ((timeBoilerOn + timeBoilerOff) / timeBoilerOn)
        except:
            dutyCycle = 0
        return int(dutyCycle)


    def createRooms(self):
        logTime = time.time()
        maxRooms = DB.getRooms()
        maxDevices = DB.getDevices()
        maxValves = DB.getValves()
        roomTemps = []
        global boilerOn
        for rooms in maxRooms:
            #print rooms
            roomValves = []
            roomNumber = rooms[0]
            roomText = rooms[1]
            for devices in maxDevices:
                if devices[4] == roomNumber:
                    for valves in maxValves:
                        valveID       = valves[0]
                        valveOpen     = valves[1]
                        valveSetPoint = valves[2]
                        valvesTemp    = valves[3]
                        valvesMode    = valves[4]
                        valvesLink    = valves[5]
                        valvesBatt    = valves[6]
                        
                        if valveID == devices[0]: # valve is in current room
                            roomDetails = (roomText,roomNumber,valveOpen,valveSetPoint,valvesTemp,valvesMode,valvesLink,valvesBatt)
                            roomValves.append(roomDetails)
                            
                            #print roomValves
            wallTemp = 999
            for i in roomValves:
                roomName = i[0]
                roomSetpoint = i[3]
                actualTemp = i[4]
                roomMode = i[5]
                if i[2] == 999:
                    wallTemp = i[4]
                else:
                    roomOpen = i[2]
            if wallTemp != 999:
                actualTemp = wallTemp
            msg = (roomName,logTime,roomSetpoint,actualTemp,roomOpen,roomMode)
            roomTemps.append(msg)
        return roomTemps
        
    def pageTop(self):
        webRefresh, baseFontSize = VAR.readVariables(['PageRefresh', 'BaseFontSize'])
        pageText = []
        pageText.append("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">""")
            
        pageText.append("""
            <meta http-equiv="refresh" content="{}; URL=index.html" >""".format(webRefresh))
            
            
        pageText.append("""
            <META HTTP-EQUIV="PRAGMA" CONTENT="NO-CACHE">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
            <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
            
            <link href="docs/css/bootstrap.min.css" rel="stylesheet">
            <link href="docs/css/highlight.css" rel="stylesheet">
            <link href="dist/css/bootstrap3/bootstrap-switch.css" rel="stylesheet">
            <link href="http://getbootstrap.com/assets/css/docs.min.css" rel="stylesheet">
            <link href="docs/css/main.css" rel="stylesheet">
            
            <link rel="stylesheet" type="text/css" media="screen"
            href="http://tarruda.github.com/bootstrap-datetimepicker/assets/css/bootstrap-datetimepicker.min.css">
             
            <script>
              var _gaq = _gaq || [];
              _gaq.push(['_setAccount', 'UA-43092768-1']);
              _gaq.push(['_trackPageview']);
              (function () {
                var ga = document.createElement('script');
                ga.type = 'text/javascript';
                ga.async = true;
                ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
                var s = document.getElementsByTagName('script')[0];
                s.parentNode.insertBefore(ga, s);
              })();
              
              function sleep(milliseconds) {
                  var start = new Date().getTime();
                  for (var i = 0; i < 1e7; i++) {
                    if ((new Date().getTime() - start) > milliseconds){
                      break;
                    }
                  }
                }
                
              function refreshPage() {
                  sleep(2000);
                  window.history.go(0);
              }
              
                function load_index(){
                    sleep(2000);
                    document.getElementById("content").innerHTML='<object type="text/html" data="index.html" ></object>';
                }
              
                  $(document).ready(function(){
                    $('.dropdown-toggle').dropdown()
                    
                });
                
                $(".dropdown-menu li a").click(function(){
                  var selText = $(this).text();
                  $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
                });
                
                $("#btnSearch").click(function(){
                    alert($('.btn-select').text()+", "+$('.btn-select2').text());
                });
                

            </script>
            <style>
            
                .btn-group.btn {   border: 0;   padding: 0; }
                .btn-group.btn > .btn { border-radius: 0 }
                .btn-group.btn > .dropdown-menu {  text-align: left; }
                .btn-group.btn:first-child > .btn {
                  -webkit-border-radius: 4px 0 0 4px;
                     -moz-border-radius: 4px 0 0 4px;
                          border-radius: 4px 0 0 4px;
                }
                
                .btn-group.btn:last-child > .btn {
                  -webkit-border-radius: 0 4px 4px 0;
                     -moz-border-radius: 0 4px 4px 0;
                          border-radius: 0 4px 4px 0;
                }
            
                container {
                    width: 337px;
                    border: 1px solid black;
                    display: inline-block;
                }
                
                block {
                    display: inline-block;
                    width: 100px;
                    height: 100px;
                    margin: 5px;
                    background: red;
                    float: right;
                }
                
                .container-filler {
                    height:600px;
                    background-color: #1abc9c;
                }
                
                block[v2] {
                    height: 210px;
                }
                
                block[h2] {
                    width: 210px;
                }
                .modal-content{
                    background-color: #6495ED;
                }
                .table {
                    font-size: 24px
                }
                
                .form-horizontal {
                    font-size: 16px
                }
                .form-control {
                    font-size: 16px
                }
                .hidden {
                    display:none;
                }
                .bg-1 {
                    background-color: #1abc9c; /* Green */
                    color: #ffffff;
                }
                .bg-2 { 
                    background-color: #474e5d; /* Dark Blue */
                    color: #ffffff;
                    vertical-align: middle;
                }
                .bg-3 { 
                    background-color: #ddd; /* Grey */
                    color: #555555;
                }
                .container-fluid {
                    padding-top: 10px;
                    padding-bottom: 10px;
                }
                h2 {
                    font-size: %svw
                }
                
                .parent {
                    display: table;
                    table-layout: fixed;
                }
                
                .child {
                    display:table-cell;
                    vertical-align:middle;
                    text-align:center;
                    float: none;
                }
                
              </style>
        </head>
        <body onload=display_ct();>""" % baseFontSize)
        html_text = ''.join(pageText)
        return html_text
    
    
    def pageHeader(self, pageType):
        
        if pageType == 'Main UI':
            buttonText = """<a href="/admin.html" class="btn btn-warning btn-md" role="button">Admin Page</a>"""
        else:
            buttonText = """<a href="/index.html" class="btn btn-warning btn-md" role="button">Main UI</a>"""
        
        webRefresh, heat_Interval, boiler_enabled = VAR.readVariables(['PageRefresh', 'Interval', 'BoilerEnabled'])
        
        theTime = self.OnUpdateTime()
        if boiler_enabled != 1:
            heat_Interval = heat_Interval * 2
        html_text = """
        <div class="container-fluid bg-2 text-center">
            <div class="row parent">
                <div class="col-sm-1 child">
                    {}
                </div>
                <div class="col-sm-10 child">
                    <h2>Heating Status @ {} <span class="badge">{}</span></h2>
                </div>
                <div class="col-sm-1 child">
                    <a href="/index.html" class="btn btn-primary" role="button">Refresh Page <span class="badge">{}</span></a>
                </div>
            </div>
        </div>
        <main id="content" role="main">""".format(buttonText, theTime, heat_Interval, webRefresh)
        return html_text
    
    def roomTable(self, roomTemps):
        baseFontSize = float(VAR.readVariables(['BaseFontSize']))
        pageText = []
        pageText.append("""
            <div class="container-fluid bg-3">
            <div class="btn-group btn-group-justified">
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>HOUSE MODE</B></a>
                <a href="/automode?auto?00?0" class="btn btn-default btn-lg" style="font-size: {0}vw;"><span class="glyphicon glyphicon-time"></span><B> AUTO</B></a>
                <a href="/ecomode?eco?0?0" class="btn btn-default btn-lg" style="font-size: {0}vw;"><span class="glyphicon glyphicon-leaf"></span><B> ECO</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><span class="glyphicon glyphicon-asterisk"></span><B> COMFORT</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><span class="glyphicon glyphicon-pencil"></span><B> CUSTOM</B></a>
            </div>
            <div class="btn-group btn-group-justified">
                <a href="/rangegraph.html" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>ROOM</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>MODE</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>SET TEMP &#8451</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>TEMP &#8451</B></a>
                <a href="#" class="btn btn-default btn-lg" style="font-size: {0}vw;"><B>VALVE %</B></a>
            </div>
              """.format(baseFontSize - 1.2))
        for rooms in roomTemps:
            roomText = rooms[0]
            setTemp  = rooms[2]
            truTemp  = rooms[3]
            valvePos = rooms[4]
            roomMode = rooms[5]
            roomModes = ['AUTO', 'MANUAL', 'ECO', 'BOOST', 'VACATION']
            if valvePos > 60:      # how far valve is open
                cold_text = 'btn-info'
            else:
                cold_text = 'btn-warning'
            # Add Room Buttons
            pageText.append("""
                <div class="btn-group btn-group-justified">
                    <div class="btn btn-group">
                        <a class="btn btn-primary btn-lg dropdown-toggle" data-toggle="dropdown" href="#"
                        style="font-size: {}vw;">
                        {} 
                        <span class="caret"></span>
                    </a>
                    <ul class="dropdown-menu">
                        """.format(baseFontSize - 1.2, roomText[0:12]))
            for i in range(1, 7):
                pageText.append("""<li><a href="/graph?{0}?{1}">Graph {1} - Day(s)</a></li>
                        """.format(roomText,i))

            pageText.append("""</ul>
                        </div>""")
            #Add Mode buttons
            pageText.append("""
            <div class="btn-group">
                <a class="btn {0} btn-lg dropdown-toggle btn-mode" data-toggle="dropdown" href="#"
                style="font-size: {2}vw;">
                {1}
                <span class="caret"></span>
            </a>
            <ul class="dropdown-menu">
                """.format(cold_text,roomMode,baseFontSize - 1.2))
            
            for mode in roomModes:
                pageText.append("""<li><a href="/mode?{0}?{1}?{2}">{0}</a></li>
                """.format(mode, roomText, setTemp))

            pageText.append("""</ul>
            </div>""")
            
            #Add Set Temperature Buttons
            pageText.append("""
            <div class="btn btn-group">
                <a class="btn {} btn-lg dropdown-toggle" data-toggle="dropdown" href="#"
                style="font-size: {}vw;">
                {} 
                <span class="caret"></span>
            </a>
            <ul class="dropdown-menu">
                """.format(cold_text,baseFontSize - 1.2, setTemp))
            
            for i in range(20, 50):
                pageText.append("""<li><a href="/mode?{0}?{1}?{2}">{2}</a></li>
                """.format(roomMode, roomText, float(i)/2))

            pageText.append("""</ul>
                        </div>""")                                 
            
            pageText.append("""
            <a href="#" class="btn {0} btn-lg" style="font-size: {5}vw;">{3}</a>
            <a href="#" class="btn {0} btn-lg" style="font-size: {5}vw;">{4}</a>
        </div>
        """.format(cold_text,roomText,setTemp,truTemp,valvePos,baseFontSize - 1.2))
        pageText.append("""
        </div>""")
        maxLayout = ''.join(pageText)
        return maxLayout
    
    
    def buttonLayout(self):
        buttonSize = 1.4
        try:
            heating_state     = DB.getBoiler()[2]
        except:
            heating_state = 0
        duty_cycle = DB.getCubes()[3]

        boiler_state, cube_state, active_cube, vera_state, baseFontSize, roomsCorrect = VAR.readVariables(['BoilerEnabled',
                                                                                             'CubeOK',
                                                                                             'ActiveCube',
                                                                                             'VeraOK',
                                                                                             'BaseFontSize',
                                                                                             'RoomsCorrect'])
        heating_cycle = self.dutyCycle()

        
        if boiler_state:
            boilerIsOn = 'btn-success btn-md" name="boilerswitch" value="Boiler Enabled" style="font-size: {}vw;">'.format(baseFontSize - buttonSize)
        else:
            boilerIsOn = 'btn-info btn-md" name="boilerswitch" value="Boiler Disabled" style="font-size: {}vw;">'.format(baseFontSize - buttonSize)
            
        if heating_state:
            heatIsOn = 'btn-danger btn-md" style="font-size: {}vw;">Heating is ON '.format(baseFontSize - buttonSize)
        else:
            heatIsOn = 'btn-info btn-md" style="font-size: {}vw;">Heating is OFF '.format(baseFontSize - buttonSize)
            
        print "Cube state {}".format (cube_state)
        if cube_state == 1:
            cubeIsOn = 'btn-success btn-md" style="font-size: {}vw;">Cube{} '.format(baseFontSize - buttonSize, active_cube)
        elif cube_state == 0:
            cubeIsOn = 'btn-warning btn-md" style="font-size: {}vw;">Cube{} '.format(baseFontSize - buttonSize, active_cube)
        if not roomsCorrect:
            cubeIsOn = 'btn-danger btn-md" style="font-size: {}vw;">Cube{} '.format(baseFontSize - buttonSize, active_cube)
            
        if vera_state:
            veraIsOn = 'btn-success btn-md" style="font-size: {}vw;">Vera'.format(baseFontSize - buttonSize)
        else:
            veraIsOn = 'btn-warning btn-md" style="font-size: {}vw;">Vera'.format(baseFontSize - buttonSize)
            
        html_text = """
    <div class="container-fluid bg-2 text-center">
        <iframe src="nowhere" class="hidden" name="sneaky">
        </iframe>
        <form action="." method="GET" target="sneaky">
        <input type="hidden" name="confirm" value="1" />
        <div class="btn-group">
            <input type="submit" class="btn {0}
            <a href="/heatcheck" class="btn {1}<span class="badge" style="font-size: {6}vw;">{2}%</span></a>
            <button type="button" class="btn {3}<span class="badge" style="font-size: {6}vw;">{4}</span></button>
            <button type="button" class="btn {5}</button>
        </form>
        </div>
    </div>
          """.format(boilerIsOn,heatIsOn,heating_cycle,cubeIsOn,duty_cycle,veraIsOn,baseFontSize - 1.8)
        return html_text
    
    def variablesPage(self):
        pageText = []
        pageText.append("""<div class="container-fluid bg-2">
            <form class="form-horizontal" role="form" action="/admin" method="POST">""")
        variables = VAR.variableData()
        for item in variables:
            if len(item) > 3:
                _text = item.split(',')
                pageText.append("""
                <div class="form-group">
                    <label class="control-label col-xs-3" for="{0}">{0}:</label>
                        <div class="col-xs-9">
                            <input type="text" class="form-control" id="{0}" name="{0}" value="{1}">
                        </div>
                    </div>
                """.format(_text[0],_text[1]))
                
        pageText.append("""
        <div class="container-fluid text-center">
            <input type="submit" class="btn btn-default btn-lg onClick="refreshPage();" id="submit" value="Submit Changes" />
                </div>
            </form>
        </div>""")
            
        html_text = ''.join(pageText)
        return html_text
    
    def shutdownButton(self):
        html_text = """
        <div class="container-fluid bg-1 text-center">
            <!-- Trigger the modal with a button -->
            <button type="button" class="btn btn-danger btn-lg" data-toggle="modal" data-target="#myModal">Shutdown or Reboot Raspberry Pi</button>

            <!-- Modal -->
            <div class="modal fade" id="myModal" role="dialog">
                <div class="modal-dialog bg-2">
    
                    <!-- Modal content-->
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal">&times;</button>
                            <h3 class="modal-title">Are you sure you want to Shutdown?</h3>
                        </div>
                        <div class="modal-body">
                            <p>This only works if running on Raspberry Pi</p>
                            <div class="btn-group btn-group-lg">
                                <a href="/restartpython" class="btn btn-primary" role="button"><strong>Restart Python</strong></a>
                                <a href="/killpython" class="btn btn-primary" role="button"><strong>Kill Python</strong></a>
                                <a href="/shutdown" class="btn btn-danger" role="button"><strong>SHUTDOWN</strong></a>
                                <a href="/reboot" class="btn btn-warning" role="button"><strong>REBOOT</strong></a>
                                </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                        </div>
                    </div>
      
                </div>
            </div>
        </div>
        """
        return html_text
    
    def weatherWidget(self):
        weather_widget = VAR.readVariables(['WeatherWidget'])
        html_text = """
        <div class="container-fluid bg-3 text=center">
        <iframe id="forecast_embed" type="text/html" frameborder="0" height="245" width="100%" src="{}">
        </iframe>
        </div>
        """.format(weather_widget)
        return html_text
    
    def keyPad(self):
        html_text = """
        <container>
            <block>9</block>
            <block>8</block>
            <block>7</block>
            <block>6</block>
            <block>5</block>
            <block>4</block>
            <block>3</block>
            <block>2</block>
            <block>1</block>
            <block>X</block>
            <block h2="">0</block>
        </container>
        """
        return html_text
    
    def filler(self):
        html_text = """
        <div class="container-filler bg-3 text=center">
        </div>
        """
        return html_text
    
    def page_bottom(self):
        html_text = """
        </main>
        <script src="docs/js/jquery.min.js"></script>
        <script src="docs/js/bootstrap.min.js"></script>
        <script src="docs/js/highlight.js"></script>
        <script src="dist/js/bootstrap-switch.js"></script>
        <script src="docs/js/main.js"></script>
        
        <script type="text/javascript"
         src="http://tarruda.github.com/bootstrap-datetimepicker/assets/js/bootstrap-datetimepicker.min.js">
        </script>
        <script type="text/javascript"
         src="http://tarruda.github.com/bootstrap-datetimepicker/assets/js/bootstrap-datetimepicker.pt-BR.js">
        </script>
        <script type="text/javascript">
          $('#datetimepicker').datetimepicker({
            format: 'dd/MM/yyyy hh:mm:ss',
            language: 'pt-BR'
          });
        </script>
        
    </body>
</html>"""
        return html_text