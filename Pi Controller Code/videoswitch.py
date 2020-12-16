

import time
import termios
import serial

# ANI-MV9 output options
# Setup output mode:(
# 1:one image;
# 2:two images 1;
# 3:two images 2;
# 4:four images 1;
# 5:four images 2;
# 6:four images 3;
# 7:four images 4;
# 8:nine images)

#video switch class

class videoswitch(object):
	def __init__(self):
		port = '/dev/VideoSwitch'		#mapped from ID 0403:6001 FTDI USB-Serial adapter
		self.default_QUAD=[1,2,3,9]
		self.default_NINE=[1,2,3,4,5,6,7,8,9]
		self.mode2=0	#0 or 1
		self.mode4=0	#0,1,2 or 3
		self.pip_toggle=False
		self.pip_toggle_enabled=False
		self.switcher = serial.Serial(port, 115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,timeout=1)
		if self.switcher:
			print "Video Switcher Serial Port opened successflly!"
		else:
			print "Error opening video switcher Serial Port"
		self.select_nine([],0)		#setup 9-way for default 1-9 values, useful for debug
	
	def configure_modes(self,_mode2,_mode4,_default_QUAD,_default_NINE,_pip_toggle_enabled):
		print "vidswitch configured:"
		self.default_QUAD=_default_QUAD
		#print _default_QUAD
		#print _default_NINE
		self.default_NINE=_default_NINE
		self.mode2=_mode2	#0 or 1
		#print _mode2
		self.mode4=_mode4	#0,1,2 or 3
		#print _mode4
		self.pip_toggle_enabled=_pip_toggle_enabled
		#print _pip_toggle_enabled
		#print "\n"

	def toggle_pip(self):
		self.pip_toggle = not self.pip_toggle
		

	def set_dual(self):
		mode=2+self.mode2
		cmd = "s mode "+str(mode)+"!"
		self.switcher.write(cmd)	
		time.sleep(0.25)

	def set_quad(self):
		mode=4+self.mode4
		cmd = "s mode "+str(mode)+"!"
		self.switcher.write(cmd)	
		time.sleep(0.25)

	def select_single(self,channel):
		cmd = "s mode 1!"
		#print "CMD: "+cmd
		self.switcher.write(cmd)
		#print self.switcher.readline()
		time.sleep(0.1)
		cmd= "s "+str(channel+1)+" v 1!"
		self.switcher.write(cmd)
		time.sleep(0.1)

	def select_dual(self,userlist,num_users):
		#print userlist
		mode=2+self.mode2
		if mode==3:
			if self.pip_toggle_enabled:
				if self.pip_toggle:
					userlist = userlist[1:] + userlist[:1]
					#print userlist
		cmd = "s mode "+str(mode)+"!"
		self.switcher.write(cmd)
		time.sleep(0.25)
		n=1
		for user in userlist:
			cmd= "s "+str(user+1)+" v "+str(n)+"!"
			self.switcher.write(cmd)
			time.sleep(0.1)
			n=n+1

	def select_quad(self,userlist,num_users):
		mode=4+self.mode4
		cmd = "s mode "+str(mode)+"!"
		self.switcher.write(cmd)	
		time.sleep(0.25)
		n=1
		print "Quad Userlist"
		print userlist
		for user in userlist:
			cmd= "s "+str(user+1)+" v "+str(n)+"!"
			self.switcher.write(cmd)
			time.sleep(0.1)
			n=n+1
		print "Num_users"+str(num_users)
		for i in range(4-num_users):
			cmd= "s "+str(self.default_QUAD[(n+i)-1])+" v "+str(n+i)+"!"
			self.switcher.write(cmd)
			time.sleep(0.1)


	def select_nine(self,userlist,num_users):
		cmd = "s mode 8!"
		self.switcher.write(cmd)
		time.sleep(0.25)
		n=1
		for user in userlist:
			cmd= "s "+str(user+1)+" v "+str(n)+"!"
			self.switcher.write(cmd)
			time.sleep(0.1)
			n=n+1
		for i in range(9-num_users):
			cmd= "s "+str(self.default_NINE[i])+" v "+str(n+i)+"!"
			self.switcher.write(cmd)
			time.sleep(0.1)

	def test(self):
		cmd = "help!"
		self.switcher.write(cmd)
		print self.switcher.readlines()

	def reset(self):
		#self.switcher.write('s factory reset!')
		#print self.switcher.readline()
		#time.sleep(2)
		#self.switcher.write('s output 3!')
		#print self.switcher.readline()
		#time.sleep(0.5)
		self.switcher.write('s beep off!')
		print self.switcher.readline()
		time.sleep(0.5)


v=videoswitch()
v.reset()
#v.test()