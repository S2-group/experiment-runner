import os, serial
import datetime, time
from platform import uname

class WattsUpPro(object):
    """An integration of "Watts up? Pro" power meter: https://github.com/isaaclino/wattsup"""
    EXTERNAL_MODE = 'E'
    INTERNAL_MODE = 'I'
    TCPIP_MODE = 'T'
    FULLHANDLING = 2

    def __init__(self, port: str = None, interval=1.0):

        # Set up & check serial ports
        if port is None:
            system = uname()[0]
            if system == 'Darwin':          # OS X
                port = '/dev/tty.usbserial-A1000wT3'
            elif system == 'Linux':
                port = '/dev/ttyUSB0'

        if not os.path.exists(port):
                print( '')
                print( 'Serial port %s does not exist.' % port)
                print( 'Please make sure FTDI drivers are installed')
                print( ' (http://www.ftdichip.com/Drivers/VCP.htm)')
                print( 'Default port is /dev/ttyUSB0 for Linux')
                raise RuntimeError("Invalid port")

        self.s = serial.Serial(port, 115200 )
        self.logfile = None
        self.interval = interval
        # initialize lists for keeping data
        self.t = []
        self.power = []
        self.potential = []
        self.current = []

    def mode(self, runmode):
        temp = '#L,W,3,%s,,%d;' % (runmode, self.interval)
        self.s.write( str.encode(temp))
        if runmode == self.INTERNAL_MODE:
            self.s.write('#O,W,1,%d' % self.FULLHANDLING)

    def log(self,timeout, logfile = None):
        print('Logging...')
        self.mode(self.EXTERNAL_MODE)
        if logfile:
            self.logfile = logfile
            o = open(self.logfile,'w')

        line = self.s.readline()
        n = 0
        timeout_start = time.time()
        

        while time.time() < timeout_start + timeout:
            if line.startswith( str.encode('#d') ):
                fields = line.split(str.encode(','))
                if len(fields)>5:
                    W = float(fields[3]) / 10
                    V = float(fields[4]) / 10
                    A = float(fields[5]) / 1000
                   
                    if self.logfile:
                        o.write('%s %d %3.1f %3.1f %5.3f\n' % (datetime.datetime.now(), n, W, V, A))  # SAVE TO LOG
                    n += self.interval
            line = self.s.readline()

        try:
            o.close()
        except:
            pass
