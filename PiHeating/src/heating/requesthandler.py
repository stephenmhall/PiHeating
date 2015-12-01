#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
from os import curdir, sep, system, execl
from sys import platform as _platform, executable, argv
from database import DbUtils
DB=DbUtils()
from webui import CreateUIPage
from graphing import MakeGraph
CUI = CreateUIPage()
GRAPH = MakeGraph()



#class MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
class MyRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        roomTemps = CUI.createRooms()
        print 'GET ',self.path
        if self.path=="/":
            self.path="/index.html"
            self.updateUIPages(roomTemps)
            
        elif self.path[0:6] == '/graph':
            roomName = self.path
            GRAPH.createGraph(roomName)
            self.path="/graph.html"
            
        elif self.path =="/?confirm=1&boilerswitch=Boiler+Enabled":
            DB.updateBoilerState(0)
            #self.path = "/index.html"
            self.updateUIPages(roomTemps)
            
        elif self.path == '/?confirm=1&boilerswitch=Boiler+Disabled':
            DB.updateBoilerState(1)
            #self.path = "/index.html"
            self.updateUIPages(roomTemps)
            
        elif self.path =="/admin":
            self.path = "/admin.html"
            self.updateUIPages(roomTemps)
            
        elif self.path == "/shutdown":
            if _platform == "linux" or _platform == "linux2":
                print 'In Linux so shutting down'
                self.path = "/shutdown.html"
                system("sudo shutdown -h now")
            elif _platform == "win32":
                print 'In Windows, Not shutting down'
                self.path = "/admin.html"
                
        elif self.path == "/reboot":
            if _platform == "linux" or _platform == "linux2":
                print 'In Linux so rebooting'
                self.path = "/shutdown.html"
                system("sudo reboot")
            elif _platform == "win32":
                print 'In Windows, Not rebooting'
                self.path = "/admin.html"
                
        elif self.path == "/killpython":
            if _platform == "linux" or _platform == "linux2":
                print 'In Linux so killing Python'
                self.path = "/shutdown.html"
                system("sudo pkill python")
            elif _platform == "win32":
                print 'In Windows, Not stopping python'
                self.path = "/admin.html"
                
        elif self.path == "/Restartpython":
            if _platform == "linux" or _platform == "linux2":
                print 'In Linux so killing Python'
                self.path = "/admin.html"
                #system("sudo pkill python")
                self.restart_program()
            elif _platform == "win32":
                print 'In Windows, Not stopping python'
                self.path = "/admin.html"
        

        try:
            #Check the file extension required and
            #set the right mime type

            sendReply = False
            if self.path.endswith(".html"):
                mimetype='text/html'
                sendReply = True
            if self.path.endswith(".jpg"):
                mimetype='image/jpg'
                sendReply = True
            if self.path.endswith(".gif"):
                mimetype='image/gif'
                sendReply = True
            if self.path.endswith(".js"):
                mimetype='application/javascript'
                sendReply = True
            if self.path.endswith(".css"):
                mimetype='text/css'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                f = open(curdir + sep + self.path) 
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

        
    def do_POST(self):
        roomTemps = CUI.createRooms()
        #print 'POST ', self.path
        if self.path == "/admin":
            self.path = "/admin.html"
            form = cgi.FieldStorage(
                fp=self.rfile, 
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                         'CONTENT_TYPE':self.headers['Content-Type'],
            })
            #print form.keys()
            boiler_enabled = DB.getVariables()[5]
            #print 'variables update boiler ', boiler_enabled
            print_enable = 0
            max_ip          = form['maxip'].value
            max_port        = form['maxport'].value
            vera_address    = form['veraaddress'].value
            vera_device     = form['veradevice'].value
            valve_interval  = form['interval'].value
            web_ip          = form['webip'].value
            web_port        = form['webport'].value
            page_refresh    = form['pagerefresh'].value
            graph_period    = form['graphperiod'].value
                
            variableList = DB.getVariables()[1:]
            cube_ok = variableList[9]
            vera_ok = variableList[10]
            
            graphPeriod = graph_period
            print 'saving graphPeriod as : ', graphPeriod
            
            msg = max_ip,max_port,vera_address,vera_device,boiler_enabled,valve_interval,print_enable,web_ip,web_port,cube_ok,vera_ok,page_refresh
            #print msg
        
            for i in range(0, len(msg)):
                if str(msg[i]) != str(variableList[i]):
                    print msg[i], variableList[i]
                    print 'not equal saving DB'
                    DB.updateVariables(msg)
                    break
    
            self.updateUIPages(roomTemps)    
        
        try:

            sendReply = False
            if self.path.endswith(".html"):
                mimetype='text/html'
                sendReply = True
            if self.path.endswith(".jpg"):
                mimetype='image/jpg'
                sendReply = True
            if self.path.endswith(".gif"):
                mimetype='image/gif'
                sendReply = True
            if self.path.endswith(".js"):
                mimetype='application/javascript'
                sendReply = True
            if self.path.endswith(".css"):
                mimetype='text/css'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                f = open(curdir + sep + self.path) 
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
            
        return
        
    def updateUIPages(self, roomTemps):
        CUI.saveUI(roomTemps)
        #time.sleep(0.5)
        CUI.saveAdminUI()
        
    def restart_program(self):
        """Restarts the current program.
        Note: this function does not return. Any cleanup action (like
        saving data) must be done before calling this function."""
        python = executable
        execl(python, python, * argv)
        
    def postPage(self, pagePath):
        try:

            sendReply = False
            if pagePath.endswith(".html"):
                mimetype='text/html'
                sendReply = True
            if pagePath.endswith(".jpg"):
                mimetype='image/jpg'
                sendReply = True
            if pagePath.endswith(".gif"):
                mimetype='image/gif'
                sendReply = True
            if pagePath.endswith(".js"):
                mimetype='application/javascript'
                sendReply = True
            if pagePath.endswith(".css"):
                mimetype='text/css'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                f = open(curdir + sep + pagePath) 
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
