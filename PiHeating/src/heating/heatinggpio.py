from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    import RPi.GPIO as GPIO
    
#from threading import Thread
import threading
from variables import Variables
from database import DbUtils
from max import Max
from os import system


import time

myThreads = []

class HeartbeatThread(threading.Thread):
    
    def __init__(self, beat_time):
        super(HeartbeatThread, self).__init__()
        self.beat_time = beat_time
        self._stop = threading.Event()
        
    def stop(self):
        self._stop.set()
        print 'setting heartbeat stop event to YES'
        
    def stopped(self):
        return 'Thread stop condition : ',self._stop.is_set()
    
    def run(self):
        #print 'heating state: ', heating_state
        # Set Cube Lights
        heart = GPIO.PWM(27, 100)
        pause_time = 0.02
        startTime = time.time()
        endTime = startTime + self.beat_time
        heart.start(0)
        while startTime < endTime:
            for i in range(0,101):      # 101 because it stops when it finishes 100  
                heart.ChangeDutyCycle(i)  
                time.sleep(pause_time)  
            for i in range(100,-1,-1):      # from 100 to zero in steps of -1  
                heart.ChangeDutyCycle(i)  
                time.sleep(pause_time)
            startTime = time.time()
            if self._stop.is_set():
                print 'heartbeat stop event is YES'
                break
        
        print 'stopping thread'
        heart.stop()
        GPIO.output(04,GPIO.LOW)
        GPIO.output(17,GPIO.LOW)
        GPIO.output(18,GPIO.LOW)
        GPIO.output(22,GPIO.LOW)
        GPIO.output(23,GPIO.LOW)
        GPIO.output(24,GPIO.LOW)
        GPIO.output(25,GPIO.LOW)
        GPIO.output(27,GPIO.LOW)
        return

class MyGpio(object):
    '''
    classdocs
    '''

    def setupGPIO(self):
        '''
        Constructor
        '''
        if _platform == "linux" or _platform == "linux2":
                
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(04,GPIO.OUT) # Boiler Disabled
            GPIO.setup(17,GPIO.OUT) # Heat ON
            GPIO.setup(18,GPIO.OUT) # Heat Off
            GPIO.setup(22,GPIO.OUT) # Cube OK
            GPIO.setup(23,GPIO.OUT) # Cube Error
            GPIO.setup(24,GPIO.OUT) # Vera Ok
            GPIO.setup(25,GPIO.OUT) # Vera Error
            GPIO.setup(27,GPIO.OUT) # Heart beat
            GPIO.setup(05,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Disable Heat Button
            GPIO.setup(06,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Check Heat
            GPIO.setup(12,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 
            GPIO.setup(13,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Reboot Raspberry Pi
#             
#             
            GPIO.add_event_detect(05,GPIO.FALLING, callback=self.buttonDisableBoiler, bouncetime=500)# 05
            GPIO.add_event_detect(06,GPIO.FALLING, callback=self.buttonCheckHeat, bouncetime=500)    # 06
            GPIO.add_event_detect(12,GPIO.FALLING, callback=self.buttonShutdown, bouncetime=500)     # 12
            GPIO.add_event_detect(13,GPIO.FALLING, callback=self.buttonReboot, bouncetime=500)       # 13
        

    def buttonDisableBoiler(self, channel):
        print 'Button Disable Boiler pressed'
        boilerState = Variables().readVariables(['BoilerEnabled'])
        if boilerState == 1:
            boilerState = 0
        else:
            boilerState = 1
        Variables().writeVariable([['BoilerEnabled', boilerState]])
        
        # Set Boiler State
        if boilerState:
            print 'GPIO boiler on'
            GPIO.output(04,GPIO.LOW)
        else:
            print 'GPIO boiler off'
            GPIO.output(04,GPIO.HIGH)
        
    def buttonCheckHeat(self, channel):
        print 'button Check Heat' 
        
        GPIO.output(04,GPIO.LOW)
        GPIO.output(17,GPIO.LOW)
        GPIO.output(18,GPIO.LOW)
        GPIO.output(22,GPIO.LOW)
        GPIO.output(23,GPIO.LOW)
        GPIO.output(24,GPIO.LOW)
        GPIO.output(25,GPIO.LOW)

        
        for _ in range(4):
            GPIO.output(17,GPIO.HIGH)
            time.sleep(.2)
            GPIO.output(17,GPIO.LOW)
            GPIO.output(18,GPIO.HIGH)
            time.sleep(.2)
            GPIO.output(18,GPIO.LOW)
            GPIO.output(22,GPIO.HIGH)
            time.sleep(.2)
            GPIO.output(22,GPIO.LOW)
        
        Max().checkHeat()
        self.setStatusLights()
    
    def buttonReboot(self, channel):
        print 'button Reboot'
        buttonPressTimer = 0
        while True:
            if (GPIO.input(channel) == False):
                buttonPressTimer += 1
                if buttonPressTimer > 4:
                    print 'rebooting'
                    ledFlash = GPIO.PWM(23, 30)
                    ledFlash.start(50)
                elif buttonPressTimer == 2:
                    ledFlash = GPIO.PWM(23, 5)
                    ledFlash.start(50)
                elif buttonPressTimer == 3:
                    ledFlash = GPIO.PWM(23, 10)
                    ledFlash.start(50)
                elif buttonPressTimer < 3:
                    ledFlash = GPIO.PWM(23, 2)
                    ledFlash.start(50)
            else:
                if buttonPressTimer > 4:
                    print 'rebooting NOW'
                    system("sudo reboot")
                elif buttonPressTimer <= 4:
                    print 'not long enough press for reboot'
                buttonPressTimer = 0
                ledFlash.stop()
                self.setStatusLights()
                break
            time.sleep(1)
        
        
        
    
    def buttonShutdown(self, channel):
        print 'button Shutdown', channel
        buttonPressTimer = 0
        while True:
            if (GPIO.input(channel) == False):
                buttonPressTimer += 1
                if buttonPressTimer > 4:
                    print 'shutting down'
                    ledFlash = GPIO.PWM(25, 30)
                    ledFlash.start(50)
                elif buttonPressTimer == 2:
                    ledFlash = GPIO.PWM(25, 5)
                    ledFlash.start(50)
                elif buttonPressTimer == 3:
                    ledFlash = GPIO.PWM(25, 10)
                    ledFlash.start(50)
                elif buttonPressTimer < 3:
                    ledFlash = GPIO.PWM(25, 2)
                    ledFlash.start(50)
            else:
                if buttonPressTimer > 4:
                    print 'shutting down NOW'
                    system("sudo shutdown -h now")
                elif buttonPressTimer <= 4:
                    print 'not long enough press for shutdown'
                buttonPressTimer = 0
                ledFlash.stop()
                self.setStatusLights()
                break
            time.sleep(1)
                    
            
        

    def heartbeat(self, beatTime):
        self.setStatusLights()
        if _platform == "linux" or _platform == "linux2":
            
            print 'GPIO for :', beatTime
            self.heartbeat_thread = HeartbeatThread(beatTime)
            self.heartbeat_thread.start()
            self.heartbeat_thread.join()
        elif _platform == "win32":
            print 'heartbeat for :', beatTime
            
    def setStatusLights(self):
        cube_state, vera_state, boiler_enabled = Variables().readVariables(['CubeOK', 'VeraOK', 'BoilerEnabled'])
        heating_state = DbUtils().getBoiler()[2]
        if cube_state:
            #print 'GPIO cube ok'
            GPIO.output(22,GPIO.HIGH)
            GPIO.output(23,GPIO.LOW)
        else:
            #print 'GPIO cube error'
            GPIO.output(22,GPIO.LOW)
            GPIO.output(23,GPIO.HIGH)
            
        # Set Vera Lights
        if vera_state:
            #print 'GPIO vera ok'
            GPIO.output(24,GPIO.HIGH)
            GPIO.output(25,GPIO.LOW)
        else:
            GPIO.output(24,GPIO.LOW)
            GPIO.output(25,GPIO.HIGH)
            #print 'GPIO vera error'
            
        # Set Heating State
        if heating_state:
            #print 'GPIO heating on'
            GPIO.output(17,GPIO.HIGH)
            GPIO.output(18,GPIO.LOW)
        else:
            #print 'GPIO heating off'
            GPIO.output(17,GPIO.LOW)
            GPIO.output(18,GPIO.HIGH)
            
        # Set Boiler State
        if boiler_enabled:
            #print 'GPIO boiler on'
            GPIO.output(04,GPIO.LOW)
        else:
            #print 'GPIO boiler off'
            GPIO.output(04,GPIO.HIGH)
            