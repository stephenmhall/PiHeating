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
        self.B_OFF = 04
        self.H_ON  = 17
        self.H_OFF = 18
        self.C_OK  = 22
        self.C_ERR = 23
        self.V_OK  = 24
        self.V_ERR = 25
        self.HBEAT = 27
        self.ON_OFF = 05
        self.CHECKH = 06
        self.SHUTDOWN = 12
        self.REBOOT   = 13

    def setupGPIO(self):
        '''
        Constructor
        '''
        self.logger.info("Setting up GPIO Pins")
        if _platform == "linux" or _platform == "linux2":
            
            
            
                
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.B_OFF,GPIO.OUT) # Boiler Disabled
            GPIO.setup(self.H_ON,GPIO.OUT) # Heat ON
            GPIO.setup(self.H_OFF,GPIO.OUT) # Heat Off
            GPIO.setup(self.C_OK,GPIO.OUT) # Cube OK
            GPIO.setup(self.C_ERR,GPIO.OUT) # Cube Error
            GPIO.setup(self.V_OK,GPIO.OUT) # Vera Ok
            GPIO.setup(self.V_ERR,GPIO.OUT) # Vera Error
            GPIO.setup(self.HBEAT,GPIO.OUT) # Heart beat
            GPIO.setup(self.ON_OFF,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Disable Heat Button
            GPIO.setup(self.CHECKH,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Check Heat
            GPIO.setup(self.SHUTDOWN,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 
            GPIO.setup(self.REBOOT,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Reboot Raspberry Pi
                  
            GPIO.add_event_detect(self.ON_OFF,GPIO.FALLING, callback=self.buttonDisableBoiler, bouncetime=500)# 05
            GPIO.add_event_detect(self.CHECKH,GPIO.FALLING, callback=self.buttonCheckHeat, bouncetime=500)    # 06
            GPIO.add_event_detect(self.SHUTDOWN,GPIO.FALLING, callback=self.buttonShutdown, bouncetime=500)     # 12
            GPIO.add_event_detect(self.REBOOT,GPIO.FALLING, callback=self.buttonReboot, bouncetime=500)       # 13
        

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
            GPIO.output(self.B_OFF,GPIO.LOW)
        else:
            self.logger.debug('GPIO boiler off')
            GPIO.output(self.B_OFF,GPIO.HIGH)
        
    def buttonCheckHeat(self, channel):
        self.logger.info('Button check heat pressed, channel %s' % channel)
        
        GPIO.output(self.B_OFF,GPIO.LOW)
        GPIO.output(self.H_ON,GPIO.LOW)
        GPIO.output(self.H_OFF,GPIO.LOW)
        GPIO.output(self.C_OK,GPIO.LOW)
        GPIO.output(self.C_ERR,GPIO.LOW)
        GPIO.output(self.V_OK,GPIO.LOW)
        GPIO.output(self.V_ERR,GPIO.LOW)

        
        for _ in range(4):
            sleepTime = 0.1
            GPIO.output(self.H_ON,GPIO.HIGH)
            time.sleep(sleepTime)
            GPIO.output(self.H_ON,GPIO.LOW)
            GPIO.output(self.H_OFF,GPIO.HIGH)
            time.sleep(sleepTime)
            GPIO.output(self.H_OFF,GPIO.LOW)
            GPIO.output(self.C_ERR,GPIO.HIGH)
            time.sleep(sleepTime)
            GPIO.output(self.C_ERR,GPIO.LOW)
            GPIO.output(self.C_OK,GPIO.HIGH)
            time.sleep(sleepTime)
            GPIO.output(self.C_OK,GPIO.LOW)
        
        Max().checkHeat()
        self.setStatusLights()
    
    def buttonReboot(self, channel):
        self.logger.info('Button Reboot pressed, channel %s' % channel)
        buttonPressTimer = 0
        while True:
            if (GPIO.input(channel) == False):
                buttonPressTimer += 1
                if buttonPressTimer > 4:
                    ledFlash = GPIO.PWM(self.C_ERR, 30)
                    ledFlash.start(50)
                elif buttonPressTimer == 2:
                    ledFlash = GPIO.PWM(self.C_ERR, 5)
                    ledFlash.start(50)
                elif buttonPressTimer == 3:
                    ledFlash = GPIO.PWM(self.C_ERR, 10)
                    ledFlash.start(50)
                elif buttonPressTimer < 3:
                    ledFlash = GPIO.PWM(self.C_ERR, 2)
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
                    ledFlash = GPIO.PWM(self.V_ERR, 30)
                    ledFlash.start(50)
                elif buttonPressTimer == 2:
                    ledFlash = GPIO.PWM(self.V_ERR, 5)
                    ledFlash.start(50)
                elif buttonPressTimer == 3:
                    ledFlash = GPIO.PWM(self.V_ERR, 10)
                    ledFlash.start(50)
                elif buttonPressTimer < 3:
                    ledFlash = GPIO.PWM(self.V_ERR, 2)
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
            
    def flashCube(self):
        t1 = threading.Thread(target=self.flashLedThread(self.C_ERR, 2, 5, 50))
        t1.start()
        t1.join()
                    
    def flashLedThread(self, channel, flashTime, frequencie, brightness):
        ledFlash = GPIO.PWM(channel, frequencie)
        ledFlash.start(brightness)
        time.sleep(flashTime)
        ledFlash.stop()
        

    def heartbeat(self, beatTime):
        self.setStatusLights()
        if _platform == "linux" or _platform == "linux2":
            try:
                self.logger.info("starting Heart Beat thread")
                self.heartbeat_thread = HeartbeatThread(beatTime)
                self.heartbeat_thread.daemon = True
                self.heartbeat_thread.start()
                self.heartbeat_thread.join()
            except Exception, err:
                self.logger.exception("Unable to start thread %s" % err)
        elif _platform == "win32":
            print 'heartbeat for :', beatTime
            
    def setStatusLights(self):
        cube_state, vera_state, boiler_enabled = Variables().readVariables(['CubeOK', 'VeraOK', 'BoilerEnabled'])
        heating_state = DbUtils().getBoiler()[2]
        self.logger.debug("setting status lights")
        if cube_state:
            GPIO.output(self.C_OK,GPIO.HIGH)
            GPIO.output(self.C_ERR,GPIO.LOW)
        else:
            GPIO.output(self.C_OK,GPIO.LOW)
            GPIO.output(self.C_ERR,GPIO.HIGH)
            
        # Set Vera Lights
        if vera_state:
            GPIO.output(self.V_OK,GPIO.HIGH)
            GPIO.output(self.V_ERR,GPIO.LOW)
        else:
            GPIO.output(self.V_OK,GPIO.LOW)
            GPIO.output(self.V_ERR,GPIO.HIGH)
            
        # Set Heating State
        if heating_state:
            GPIO.output(self.H_ON,GPIO.HIGH)
            GPIO.output(self.H_OFF,GPIO.LOW)
        else:
            GPIO.output(self.H_ON,GPIO.LOW)
            GPIO.output(self.H_OFF,GPIO.HIGH)
            
        # Set Boiler State
        if boiler_enabled:
            GPIO.output(self.B_OFF,GPIO.LOW)
        else:
            GPIO.output(self.B_OFF,GPIO.HIGH)
            self.logger.info("Starting flashing boiler light")

            