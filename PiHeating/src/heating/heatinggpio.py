from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    import RPi.GPIO as GPIO
    
import logging
import threading
from variables import Variables
from database import DbUtils
from max import checkHeat
from os import system
import time

module_logger = logging.getLogger("main.heatinggpio")

B_OFF = 04      # Boiler off LED
H_ON  = 17      # Heat On LED
H_OFF = 18      # Heat Off LED
C_OK  = 22      # Cube OK LED
C_ERR = 23      # Cube Error LED
V_OK  = 24      # Vera Ok LED
V_ERR = 25      # Vera Error LED
HBEAT = 27      # HEARTBEAT LED
ON_OFF = 05     # Boiler ON/Off button
CHECKH = 06     # Manual Valve check button
SHUTDOWN = 12   # Shutdown RPi button
REBOOT   = 13   # Reboot RPi button
BOILER_SW= 21   # Boiler relay switch output


class HeartbeatThread(object):
    """
    Runs the heartbeat thread
    """
    def __init__(self, beat_time):
        self.beat_time = beat_time
        self.logger = logging.getLogger("main.heatinggpio.heartbeatthread")
        self.logger.debug("Heartbeat Thread initialised")
        
        thread = threading.Thread(target=self.run, args=())
        #thread.daemon = True
        thread.start()
        thread.join(self.beat_time + 2)
    
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

        heart.stop()
        GPIO.output(04,GPIO.LOW)
        GPIO.output(17,GPIO.LOW)
        GPIO.output(18,GPIO.LOW)
        GPIO.output(22,GPIO.LOW)
        GPIO.output(23,GPIO.LOW)
        GPIO.output(24,GPIO.LOW)
        GPIO.output(25,GPIO.LOW)
        GPIO.output(27,GPIO.LOW)
        self.logger.debug("heartbeat thread ended")
        
def hBeat(beat_time):
    module_logger.info("starting heart beat for %s" % beat_time)
    # Set Cube Lights
    heart = GPIO.PWM(27, 100)
    pause_time = 0.02
    startTime = time.time()
    endTime = startTime + beat_time
    heart.start(0)
    while startTime < endTime:
        for i in range(0,101):      # 101 because it stops when it finishes 100  
            heart.ChangeDutyCycle(i)  
            time.sleep(pause_time)  
        for i in range(100,-1,-1):      # from 100 to zero in steps of -1  
            heart.ChangeDutyCycle(i)  
            time.sleep(pause_time)
        startTime = time.time()

    heart.stop()
    GPIO.output(04,GPIO.LOW)
    GPIO.output(17,GPIO.LOW)
    GPIO.output(18,GPIO.LOW)
    GPIO.output(22,GPIO.LOW)
    GPIO.output(23,GPIO.LOW)
    GPIO.output(24,GPIO.LOW)
    GPIO.output(25,GPIO.LOW)
    GPIO.output(27,GPIO.LOW)
    module_logger.debug("heartbeat ended")
    

def setupGPIO():
    '''
    Constructor
    '''
    module_logger.info("Setting up GPIO Pins")
    if _platform == "linux" or _platform == "linux2":
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(B_OFF,GPIO.OUT) # Boiler Disabled
        GPIO.setup(H_ON,GPIO.OUT) # Heat ON
        GPIO.setup(H_OFF,GPIO.OUT) # Heat Off
        GPIO.setup(C_OK,GPIO.OUT) # Cube OK
        GPIO.setup(C_ERR,GPIO.OUT) # Cube Error
        GPIO.setup(V_OK,GPIO.OUT) # Vera Ok
        GPIO.setup(V_ERR,GPIO.OUT) # Vera Error
        GPIO.setup(HBEAT,GPIO.OUT) # Heart beat
        GPIO.setup(BOILER_SW,GPIO.OUT) # Boiler Switch
        GPIO.setup(ON_OFF,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Disable Heat Button
        GPIO.setup(CHECKH,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Check Heat
        GPIO.setup(SHUTDOWN,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 
        GPIO.setup(REBOOT,GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Reboot Raspberry Pi
              
        GPIO.add_event_detect(ON_OFF,GPIO.FALLING, callback=buttonDisableBoiler, bouncetime=500)# 05
        GPIO.add_event_detect(CHECKH,GPIO.FALLING, callback=buttonCheckHeat, bouncetime=500)    # 06
        GPIO.add_event_detect(SHUTDOWN,GPIO.FALLING, callback=buttonShutdown, bouncetime=500)     # 12
        GPIO.add_event_detect(REBOOT,GPIO.FALLING, callback=buttonReboot, bouncetime=500)       # 13
    

def buttonDisableBoiler(channel):
    module_logger.info('Button Disable Boiler pressed, channel %s' % channel)
    boilerState = Variables().readVariables(['BoilerEnabled'])
    if boilerState == 1:
        boilerState = 0
    else:
        boilerState = 1
    Variables().writeVariable([['BoilerEnabled', boilerState]])
    
    # Set Boiler State
    if boilerState:
        module_logger.debug('GPIO boiler on')
        GPIO.output(B_OFF,GPIO.LOW)
    else:
        module_logger.debug('GPIO boiler off')
        GPIO.output(B_OFF,GPIO.HIGH)
    
def buttonCheckHeat(channel):
    module_logger.info('Button check heat pressed, channel %s' % channel)
    
    GPIO.output(B_OFF,GPIO.LOW)
    GPIO.output(H_ON,GPIO.LOW)
    GPIO.output(H_OFF,GPIO.LOW)
    GPIO.output(C_OK,GPIO.LOW)
    GPIO.output(C_ERR,GPIO.LOW)
    GPIO.output(V_OK,GPIO.LOW)
    GPIO.output(V_ERR,GPIO.LOW)

    for _ in range(4):
        sleepTime = 0.1
        GPIO.output(H_ON,GPIO.HIGH)
        time.sleep(sleepTime)
        GPIO.output(H_ON,GPIO.LOW)
        GPIO.output(H_OFF,GPIO.HIGH)
        time.sleep(sleepTime)
        GPIO.output(H_OFF,GPIO.LOW)
        GPIO.output(C_ERR,GPIO.HIGH)
        time.sleep(sleepTime)
        GPIO.output(C_ERR,GPIO.LOW)
        GPIO.output(C_OK,GPIO.HIGH)
        time.sleep(sleepTime)
        GPIO.output(C_OK,GPIO.LOW)
    
    checkHeat()
    setStatusLights()

def buttonReboot(channel):
    module_logger.info('Button Reboot pressed, channel %s' % channel)
    buttonPressTimer = 0
    while True:
        if (GPIO.input(channel) == False):
            buttonPressTimer += 1
            if buttonPressTimer > 4:
                ledFlash = GPIO.PWM(C_ERR, 30)
                ledFlash.start(50)
            elif buttonPressTimer == 2:
                ledFlash = GPIO.PWM(C_ERR, 5)
                ledFlash.start(50)
            elif buttonPressTimer == 3:
                ledFlash = GPIO.PWM(C_ERR, 10)
                ledFlash.start(50)
            elif buttonPressTimer < 3:
                ledFlash = GPIO.PWM(C_ERR, 2)
                ledFlash.start(50)
        else:
            if buttonPressTimer > 4:
                module_logger.warning("Rebooting now")
                system("sudo reboot")
            elif buttonPressTimer <= 4:
                module_logger.info('not long enough press for reboot')
            buttonPressTimer = 0
            ledFlash.stop()
            setStatusLights()
            break
        time.sleep(1)
    
    
    

def buttonShutdown(channel):
    module_logger.info('Button Shutdown pressed, channel %s' % channel)
    buttonPressTimer = 0
    while True:
        if (GPIO.input(channel) == False):
            buttonPressTimer += 1
            if buttonPressTimer > 4:
                print 'shutting down'
                ledFlash = GPIO.PWM(V_ERR, 30)
                ledFlash.start(50)
            elif buttonPressTimer == 2:
                ledFlash = GPIO.PWM(V_ERR, 5)
                ledFlash.start(50)
            elif buttonPressTimer == 3:
                ledFlash = GPIO.PWM(V_ERR, 10)
                ledFlash.start(50)
            elif buttonPressTimer < 3:
                ledFlash = GPIO.PWM(V_ERR, 2)
                ledFlash.start(50)
        else:
            if buttonPressTimer > 4:
                module_logger.warning("Shutting down now")
                system("sudo shutdown -h now")
            elif buttonPressTimer <= 4:
                module_logger.info('not long enough press for shutdown')
            buttonPressTimer = 0
            ledFlash.stop()
            setStatusLights()
            break
        time.sleep(1)
        
def flashCube():
    t1 = threading.Thread(target=flashLedThread(C_ERR, 2, 5, 50))
    t1.start()
    t1.join()
                
def flashLedThread(channel, flashTime, frequencie, brightness):
    ledFlash = GPIO.PWM(channel, frequencie)
    ledFlash.start(brightness)
    time.sleep(flashTime)
    ledFlash.stop()
    
# def relayHeating(status):
#     module_logger.info('Manual Heating switch, status %s' % status)
#     if status == 1:
#         GPIO.output(BOILER_SW,GPIO.LOW) # Pull down Relay to switch on.
#     elif status == 0:
#         GPIO.output(BOILER_SW,GPIO.HIGH)
        
def setStatusLights():
    cube_state, vera_state, boiler_enabled, local_relay = Variables().readVariables(['CubeOK', 'VeraOK', 'BoilerEnabled', 'ManualHeatingSwitch'])
    heating_state = DbUtils().getBoiler()[2]
    module_logger.info("setting status lights")
    if cube_state:
        GPIO.output(C_OK,GPIO.HIGH)
        GPIO.output(C_ERR,GPIO.LOW)
    else:
        GPIO.output(C_OK,GPIO.LOW)
        GPIO.output(C_ERR,GPIO.HIGH)
        
    # Set Vera Lights
    if vera_state:
        GPIO.output(V_OK,GPIO.HIGH)
        GPIO.output(V_ERR,GPIO.LOW)
    else:
        GPIO.output(V_OK,GPIO.LOW)
        GPIO.output(V_ERR,GPIO.HIGH)
        
    # Set Heating State
    if heating_state:
        GPIO.output(H_ON,GPIO.HIGH)
        GPIO.output(H_OFF,GPIO.LOW)
        if local_relay:
            module_logger.info("Switching local relay")
            GPIO.output(BOILER_SW,GPIO.LOW) # Pull down Relay to switch on.
    else:
        GPIO.output(H_ON,GPIO.LOW)
        GPIO.output(H_OFF,GPIO.HIGH)
        if local_relay:
            module_logger.info("Switching local relay")
            GPIO.output(BOILER_SW,GPIO.HIGH)
        
    # Set Boiler State
    if boiler_enabled:
        GPIO.output(B_OFF,GPIO.LOW)
    else:
        GPIO.output(B_OFF,GPIO.HIGH)
        module_logger.info("Starting flashing boiler light")

        