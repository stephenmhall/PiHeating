import serial
import time
import multiprocessing
import logging

## Change this to match your local settings
SERIAL_PORT = '/dev/ttyAMA0'
SERIAL_BAUDRATE = 115200

module_logger = logging.getLogger("main.neopixelserial")

class SerialProcess(multiprocessing.Process):
 
    def __init__(self, input_queue, output_queue):
        multiprocessing.Process.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.sp = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0)
 
    def close(self):
        self.sp.close()
 
    def writeSerial(self, data):
        self.sp.write(data)
        
    def readSerial(self):
        return self.sp.readline().replace("\n", "")
 
    def run(self):
 
        self.sp.flushInput()
 
        while True:
            # look for incoming tornado request
            if not self.input_queue.empty():
                data = self.input_queue.get()
 
                # send it to the serial device
                self.writeSerial(data)
                module_logger.info("writing to serial: %s" % data)
 
            # look for incoming serial data
            if (self.sp.inWaiting() > 0):
                data = self.readSerial()
                module_logger.info("writing to serial: %s" % data)
                self.output_queue.put(data)
            time.sleep(.2)