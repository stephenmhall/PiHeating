from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    import RPi.GPIO as GPIO
    
from threading import Thread
from variables import Variables

import time

class MyGpio(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        if _platform == "linux" or _platform == "linux2":
            GPIO.cleanup()
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
            GPIO.setup(05,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Disable Heat Button
            
            GPIO.add_event_detect(05,GPIO.RISING, callback=self.buttonDisableBoiler, bouncetime=500)
        

    def buttonDisableBoiler(self, event):
        GPIO.remove_event_detect(05)
        print 'Button Disable Boiler pressed'
        boilerState = Variables().readVariables(['BoilerEnabled'])
        if boilerState == 1:
            boilerState = 0
        else:
            boilerState = 1
        
        Variables().writeVariable([['BoilerEnabled', boilerState]])
        self.boilerState(boilerState)
        time.sleep(1) # stops event repeating
        GPIO.add_event_detect(05,GPIO.RISING, callback=self.buttonDisableBoiler, bouncetime=500)
        
    
    def heartbeat(self, beatTime):
        if _platform == "linux" or _platform == "linux2":
            print 'GPIO for :', beatTime
            thread = Thread(name = 'heartbeat', target = self.beatFunction(beatTime))
            thread.setDaemon(True)
            thread.start()
            #thread.join()
        elif _platform == "win32":
            print 'heartbeat for :', beatTime
            
    def beatFunction(self, arg):
        heart = GPIO.PWM(27, 100)
        pause_time = 0.02
        startTime = time.time()
        endTime = startTime + arg
        heart.start(0)
        while startTime < endTime:
            for i in range(0,101):      # 101 because it stops when it finishes 100  
                heart.ChangeDutyCycle(i)  
                time.sleep(pause_time)  
            for i in range(100,-1,-1):      # from 100 to zero in steps of -1  
                heart.ChangeDutyCycle(i)  
                time.sleep(pause_time)
            startTime = time.time()
        
        print 'stopping thread'
        heart.stop()
        #GPIO.cleanup()
        #return
            
            
    def boilerState(self, state):
        if _platform == "linux" or _platform == "linux2":
            if state == 1:
                print 'GPIO boiler on'
                GPIO.output(04,GPIO.LOW)
            elif state == 0:
                print 'GPIO boiler off'
                GPIO.output(04,GPIO.HIGH)
                
        elif _platform == "win32":
            if state == 1:
                print 'heating on'
            elif state == 0:
                print 'heating off'
                
    def heatingState(self, state):
        if _platform == "linux" or _platform == "linux2":
            if state == 1:
                print 'GPIO heating on'
                GPIO.output(17,GPIO.HIGH)
                GPIO.output(18,GPIO.LOW)
            elif state == 0:
                print 'GPIO heating off'
                GPIO.output(17,GPIO.LOW)
                GPIO.output(18,GPIO.HIGH)
                
        elif _platform == "win32":
            if state == 1:
                print 'heating on'
            elif state == 0:
                print 'heating off'
                
    def cubeState(self, state):
        if _platform == "linux" or _platform == "linux2":
            if state == 1:
                print 'GPIO cube ok'
                GPIO.output(22,GPIO.HIGH)
                GPIO.output(23,GPIO.LOW)
            elif state == 0:
                print 'GPIO cube error'
                GPIO.output(22,GPIO.LOW)
                GPIO.output(23,GPIO.HIGH)
        elif _platform == "win32":
            if state:
                print 'cube ok'
            else:
                print 'cube error'
            
    def veraState(self, state):
        if _platform == "linux" or _platform == "linux2":
            if state == 1:
                print 'GPIO vera ok'
                GPIO.output(24,GPIO.HIGH)
                GPIO.output(25,GPIO.LOW)
            elif state == 0:
                GPIO.output(24,GPIO.LOW)
                GPIO.output(25,GPIO.HIGH)
                print 'GPIO vera error'
        elif _platform == "win32":       
            if state:
                print 'vera ok'
            else:
                print 'vera error'