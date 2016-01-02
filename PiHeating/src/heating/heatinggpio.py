from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    import RPi.GPIO as GPIO
    
import logging
import threading
from variables import Variables
from database import DbUtils
from max import Max
from os import system
import time

module_logger = logging.getLogger("main.heatinggpio")

myThreads = []

class HeartbeatThread(threading.Thread):
    
    def __init__(self, beat_time):
        super(HeartbeatThread, self).__init__()
        self.beat_time = beat_time
        self._stop = threading.Event()
        self.logger = logging.getLogger("main.heatinggpio.heartbeatthread")
        
    def stop(self):
        self._stop.set()
        print 'setting heartbeat stop event to YES'
        
    def stopped(self):
        return 'Thread stop condition : ',self._stop.is_set()
    
    def run(self):
        self.logger.info("starting heart beat for %s" % self.beat_time)
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
                self.logger.info("heartbeat stop event is YES")
                break
        
        self.logger.debug("stopping heartbeat thread")
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
    def __init__(self):
        self.logger = logging.getLogger("main.heatinggpio.MyGpio")

    def setupGPIO(self):
        '''
        Constructor
        '''
        self.logger.info("Setting up GPIO Pins")
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
        self.logger.info('Button Disable Boiler pressed, channel %s' % channel)
        boilerState = Variables().readVariables(['BoilerEnabled'])
        if boilerState == 1:
            boilerState = 0
        else:
            boilerState = 1
        Variables().writeVariable([['BoilerEnabled', boilerState]])
        
        # Set Boiler State
        if boilerState:
            self.logger.debug('GPIO boiler on')
            GPIO.output(04,GPIO.LOW)
        else:
            self.logger.debug('GPIO boiler off')
            GPIO.output(04,GPIO.HIGH)
        
    def buttonCheckHeat(self, channel):
        self.logger.info('Button check heat pressed, channel %s' % channel)
        
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
        self.logger.info('Button Reboot pressed, channel %s' % channel)
        buttonPressTimer = 0
        while True:
            if (GPIO.input(channel) == False):
                buttonPressTimer += 1
                if buttonPressTimer > 4:
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
                    self.logger.warning("Rebooting now")
                    system("sudo reboot")
                elif buttonPressTimer <= 4:
                    self.logger.info('not long enough press for reboot')
                buttonPressTimer = 0
                ledFlash.stop()
                self.setStatusLights()
                break
            time.sleep(1)
        
        
        
    
    def buttonShutdown(self, channel):
        self.logger.info('Button Shutdown pressed, channel %s' % channel)
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
                    self.logger.warning("Shutting down now")
                    system("sudo shutdown -h now")
                elif buttonPressTimer <= 4:
                    self.logger.info('not long enough press for shutdown')
                buttonPressTimer = 0
                ledFlash.stop()
                self.setStatusLights()
                break
            time.sleep(1)
                    
            
        

    def heartbeat(self, beatTime):
        self.setStatusLights()
        if _platform == "linux" or _platform == "linux2":
            self.logger.info("starting Heart Beat thread")
            self.heartbeat_thread = HeartbeatThread(beatTime)
            self.heartbeat_thread.start()
            self.heartbeat_thread.join()
        elif _platform == "win32":
            print 'heartbeat for :', beatTime
            
    def setStatusLights(self):
        cube_state, vera_state, boiler_enabled = Variables().readVariables(['CubeOK', 'VeraOK', 'BoilerEnabled'])
        heating_state = DbUtils().getBoiler()[2]
        self.logger.debug("setting status lights")
        if cube_state:
            GPIO.output(22,GPIO.HIGH)
            GPIO.output(23,GPIO.LOW)
        else:
            GPIO.output(22,GPIO.LOW)
            GPIO.output(23,GPIO.HIGH)
            
        # Set Vera Lights
        if vera_state:
            GPIO.output(24,GPIO.HIGH)
            GPIO.output(25,GPIO.LOW)
        else:
            GPIO.output(24,GPIO.LOW)
            GPIO.output(25,GPIO.HIGH)
            
        # Set Heating State
        if heating_state:
            GPIO.output(17,GPIO.HIGH)
            GPIO.output(18,GPIO.LOW)
        else:
            GPIO.output(17,GPIO.LOW)
            GPIO.output(18,GPIO.HIGH)
            
        # Set Boiler State
        if boiler_enabled:
            GPIO.output(04,GPIO.LOW)
        else:
            GPIO.output(04,GPIO.HIGH)
            self.logger.info("Starting flashing boiler light")

            