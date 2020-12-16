 

import RPi.GPIO as GPIO
import serial
import time

##//COMMS FORMAT:
##//DEVICETYPE,DEVICEID,COMMAND,LENGTH,DATA(*n),CHECKSUM


class Serial_485(object):
        def __init__(self):
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(12, GPIO.OUT)
                GPIO.output(12, 0)   

                self.types=["Null","RotatorController","AmpController"]
                self.devices=[]
                self.ValList=[]
                self.devicecount=0

                self.ser = serial.Serial(port='/dev/ttyS0',baudrate=9600,timeout=1,)       #pi3 serial port /dev/ttyS0, AMA0 on earlier versions
                self.delay = 1/9600.0*10     #per byte at 9600baud
                print "Initialised"
                self.find_devices()
                self.read_devices()


        def calc_checksum(self,data):
                sum=0
                for c in data:     
                        sum=sum^ord(c)
                sum&=0xFF
                return sum

        def find_devices(self):
                self.devicecount=0
                #search for connected devices
                for n in range(16):
                        print n
                        command = chr(2)+ chr(n)+chr(3) +chr(0)

                        chksum=0
                        for c in command:
                                chksum = chksum^ord(c)
                        command=command+chr(chksum)
                        #print "Checksum@ID:"+str(n)+"="+str(chksum)

                        GPIO.output(12, 1)
                        time.sleep(0.001)
                        self.ser.write(command)
                        #ser.flush()		#takes too long!
                        time.sleep(len(command)*self.delay)
                        GPIO.output(12, 0)
                        time.sleep(0.1)


                        info=""
                        if self.ser.inWaiting() >3:
                                #print "In buffer="+str(ser.inWaiting())
                                TYPE = self.ser.read()
                                ID = self.ser.read()
                                CMD = self.ser.read()
                                LEN = self.ser.read() 
                                for a in range(ord(LEN)):
                                        info=info+self.ser.read()
                                print info
                                CHKSUM = self.ser.read()
                                data=TYPE+ID+CMD+LEN+info
                                MYCHKSUM = self.calc_checksum(data)
                                #print "type:"+str(ord(TYPE))
                                #print "id:"+str(ord(ID))
                                #print "cmd:"+str(ord(CMD))
                                #print "length:"+str(ord(LEN))
                                #print n
                                #print "checksum:"+str(ord(CHKSUM))
                                #print "mychecksum:"+str(MYCHKSUM)
                                if ord(CHKSUM)==MYCHKSUM:
                                        print "Found ID:"+str(ord(ID))+" "+info
                                        self.devices.append([str(ord(ID)),info])
                                        
                                        self.devicecount=self.devicecount+1
                                self.ser.read(self.ser.inWaiting())               #flush
                print "find devices:"
                print self.devices


        def read_devices(self):
                self.ValList = []
                #print "devicecount:"+str(self.devicecount)
                for dev in self.devices:
                        command = chr(2)+ chr(int(dev[0]))+chr(1) +chr(0)            #read command, returns x bytes

                        chksum=0
                        for c in command:
                                chksum = chksum^ord(c)
                        command=command+chr(chksum)

                        GPIO.output(12, 1)
                        time.sleep(0.001)
                        self.ser.write(command)
                        time.sleep(len(command)*self.delay)
                        GPIO.output(12, 0)
                        time.sleep(0.05)


                        Val={}
                        if self.ser.inWaiting() >0:
                                time.sleep(0.02)
                                data = self.ser.read(self.ser.inWaiting())
                                length=len(data)
                                CHKSUM = ord(data[length-1])
                                #print CHKSUM
                                MYCHKSUM = self.calc_checksum(data[:-1])
                                #print MYCHKSUM
                                if CHKSUM==MYCHKSUM:
                                        if ord(data[0])==2:
                                                if ord(data[1])==int(dev[0]):
                                                        Val["A1"]=str(ord(data[4])<<8|ord(data[5]))
                                                        Val["A2"]=str(ord(data[6])<<8|ord(data[7]))
                                                        Val["A3"]=str(ord(data[8])<<8|ord(data[9]))
                                                        Val["T1"]=str((ord(data[10])<<8|ord(data[11]))/100.0)
                                                        Val["T2"]=str((ord(data[12])<<8|ord(data[13]))/100.0)
                                                        Val["DI"]=str(ord(data[14]))
                                                        Val["DO"]=str(ord(data[15]))
                                                        Val["ID"]=dev[0]
                                                        Val["INFO"]=dev[1]
                                                        self.ValList.append(Val)
                                                        self.ser.read(self.ser.inWaiting())               #flush

                                                        
                                else:
                                        print "Checksum error!"
                                        self.ser.read(self.ser.inWaiting()) 
                                        self.ValList.append(Val)        #null
                                

                        else:
                                self.ser.read(self.ser.inWaiting())               #flush
                                self.ValList.append(Val)        #null
                        time.sleep(0.1)
                print "read devices:"
                print self.ValList




        ## direct write to digital outputs
        def write_digital(self,id,value):
                time.sleep(0.01)
                command = chr(2)+ chr(id)+chr(2) +chr(1)+chr(value)            #read command, returns x bytes

                chksum=0
                for c in command:
                        chksum = chksum^ord(c)
                command=command+chr(chksum)
               # for c in command:
                        #print ord(c)

                GPIO.output(12, 1)
                time.sleep(0.001)
                self.ser.write(command)
                time.sleep(len(command)*self.delay)
                GPIO.output(12, 0)
                time.sleep(0.05)

        def enable_output(self,id,num):    #enable a particular output, ie bit 3 or 4 for OC or FET switch on AmpControllerBoard
                val = int(self.ValList[id]["DO"])
                if (val>>num & 1) ==0:
                        val=(val & 255-(1<<num)) | 1<<num
                        print "Comms: id:"+self.ValList[id]["ID"]
                        self.write_digital(int(self.ValList[id]["ID"]),val)
                        print "Comms: DO val:"+str(val)

        def disable_output(self,id,num):    #disable a particular output, ie bit 3 or 4 for OC or FET switch on AmpControllerBoard
                val = int(self.ValList[id]["DO"])
                if (val>>num & 1) ==1:
                        val=(val & 255-(1<<num)) 
                        self.write_digital(int(self.ValList[id]["ID"]),val)
                        print "Comms: id:"+self.ValList[id]["ID"]
                        print "Comms: DO val:"+str(val)

        def list_devices(self,devnum):
                #print "list devices request:"+str(devnum)
                #print "devices:"+str(self.devicecount)
                #print self.ValList
                if devnum>-1:
                        return self.ValList[devnum]
                else:
                        return self.ValList



'''
comms485 = Serial_485() #init comms class

#comms485.find_devices()

comms485.write_digital(1,0)
comms485.read_devices()
print "Device Count:"+str(comms485.devicecount)
for n in range(comms485.devicecount):
        print comms485.list_devices(n)["DO"]

print "After set bit"
comms485.enable_output(1,3)
comms485.read_devices()
for n in range(comms485.devicecount):
        print comms485.list_devices(n)["DO"]

'''



