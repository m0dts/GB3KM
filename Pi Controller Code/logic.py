#!/usr/bin/python
import time
from datetime import datetime
import json
import socket
import struct
import pygame
import os
import psutil
import threading
import pylcd		#https://github.com/thorrak/pi-libs
import requests	
import httplib
import netifaces
import termios
import serial
import sys
import signal

#seperate includes
from Serial_485 import Serial_485		#custom comms to external devices like PA's
from encoder import encoder				#Encoder Box stuff - messy!
from display import display				#pygame display control
from videoswitch import videoswitch		#hdmi switch control
from IO import IO						#48 GPIO over i2c
from Sync import Sync					#analog syn det
from OSD import OSD						#MX7456 OSD
from DTMF import DTMF					#DTMF input - list of chars








os.chdir("/home/pi/logic/")		#working directory


display_type="hdmi"		# composite or hdmi
if len(sys.argv)==2:
	if sys.argv[1]=="debug":
		print "\n\n>>>>>>>>>   Running in debug mode!!!!!!\n\n"
		debug=True
	else:
		debug=False
else:
	debug=False


activitytime=0
weatherpictime = 0
MetOfficeWXpictime=0
configtime = 0
scheduler_running=False
lcd_cycle=0
mix=[]
#default_QUAD=[1,2,3,9]

restart = 0
Inet_access="No"

##get IP Address
LocalIPAddress="x.x.x.x"
RemoteIPAddress= "x.x.x.x"



analog_users=0
gpio_users=[]
RepeaterInUse=True
LastRepeaterState=False
status={}
useridentpos=1

CAROUSEL=9-1

#load config file
with open('/var/www/html/io_config.json') as json_file:  
	config = json.load(json_file)
    

lastuserlist =[]		#previous 'sync' status
usercount =0

#bank 3 1st 4 bits is video switcher special buttons, channels are 1-16

delay_mode = 0.05		#screen layout
delay_ch=0.05			#video port change

#main IO register
io_register=[0,0,0,0,0,0]








#sockets ##############################

#UDP Status Socket
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#sockets ################################


	
	
#Handle ctrl-c !
def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')
	sync.stop()
	pygame.quit()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)




#check internet access
def have_internet():
    global LocalIPAddress
    global RemoteIPAddress
    global Inet_access

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        LocalIPAddress = s.getsockname()[0]
        s.close()
        try:
            req= requests.get('http://ipconfig.in/ip',timeout=5)
            if req.status_code==200:
                RemoteIPAddress= req.text.strip('\r\n')
                Inet_access= "Yes"
            else:
                RemoteIPAddress= ""
                Inet_access= "No"
        except:
            RemoteIPAddress= ""
            Inet_access= "No"
    except:
        LocalIPAddress=""



def is_interface_up(interface):
    addr = netifaces.ifaddresses(interface)
    return netifaces.AF_INET in addr






#timer for identification every 15min
class timer_id(object):
	def __init__(self):
		self.trigger=0
		self.lastmin=0
		self.lock = threading.Lock()
		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True
		thread.start()

	def run(self):
		while True:
			min = int(time.strftime("%M"))
			hour = int(time.strftime("%H"))
			if min!=self.lastmin:
				self.lastmin=min
				if min==0 or min==15 or min==30 or min==45:
					with self.lock:
						self.trigger=1
			time.sleep(0.1)
		
	def elapsed(self):
		if self.trigger>0:
			with self.lock:
				self.trigger=0
			return True
		else:
			return False
			

#re-usable repeating timer class
class repeating_timer(object):	
	def __init__(self, interval=10):
		self.interval = interval
		self.trigger=0
		self.lock = threading.Lock()
		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True
		thread.start()

	def run(self):
		while True:
			time.sleep(self.interval)
			with self.lock:
				self.trigger+=1
			
	def elapsed(self):

		if self.trigger>0:
			with self.lock:
				self.trigger=0
			return True
		else:
			return False

			
#re-usable re-settable timer class
class onetime_timer(object):	
	def __init__(self, interval=10):
		self.trigger=0
		self.lock = threading.Lock()
		self.running=True
		self.interval = interval
		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True
		self.thread.start()

	def run(self):
		while True:
			time.sleep(0.1)
			if self.running:
				time.sleep(0.1)
				with self.lock:
					self.trigger+=1
					#print self.trigger
			
	def elapsed(self):
		if self.trigger>self.interval*10:
			with self.lock:
				#self.trigger=0
				self.running=False
			return True
		else:
			return False
			
	def reset(self):
		with self.lock:
			self.trigger=0
			self.running=True

	def progress(self):
		with self.lock:
			return (float)(self.trigger/10)/(float(self.interval))	# % of timer before elapsed.


#re-usable re-settable timer class
class loop_timer(object):	
	def __init__(self, interval=3,loops=1):
		self.loop=1
		self.loops = loops
		self.lock = threading.Lock()
		self.enabled=False
		self.running=False
		self.started=False
		self.interval = interval
		self.thread = threading.Thread(target=self.run, args=())
		self.thread.daemon = True
		self.thread.start()

	def run(self):
		while True:
			if self.enabled:
				time.sleep(self.interval)
				with self.lock:
					self.loop=self.loop+1
					if self.loop>=self.loops:
						self.running=False
					self.enabled=False
			time.sleep(0.01)
			
			
	def loop_elapsed(self):		#check and reset if complete
		if self.enabled:
			return False
		else:
			with self.lock:
				if self.running:
					self.enabled=True
			return True
	
	def is_started(self):
		return self.started
		
	def is_ended(self):
		if self.loop>=self.loops:
			time.sleep(self.interval)
			with self.lock:
				self.started=False
			return True
		else:
			return False
			
	def start(self,interval,loops):
		with self.lock:
			self.loop=1
			self.interval=interval
			self.loops=loops
			self.enabled=False
			self.running=True
			self.started=True











#Set direction and pullup registers for pins using config settings
def set_Dir():
	#figure out which pins need to be inputs, use config list of 'Inputs' to see which are used and set bits for each port on i2c extenders
	direction=[0,0,0,0,0,0]
	for input in config['Inputs']:
		if input['Location']=='I2C_GPIO':
			bank = (int(input['Associated_Port'])-1)/8
			offset= int(input['Associated_Port'])-1 - bank*8
			direction[bank] = int(direction[bank]) | 1<<offset
	#print "directions..."
	print direction
	io.set_io_directions(direction)
	return direction

def io_set_bit(bank,bit):
	io_register[bank] |=1<<bit
	io.write_outputs(io_register)
	
def io_clear_bit(bank,bit):
	io_register[bank] &=~1<<bit
	io.write_outputs(io_register)
	
	



# generate a list of active inputs

def get_users():
	gpio=False
	analog=False
	system=False
	global analog_users
	global gpio_users
	global RepeaterInUse
	userlist=[]
	mixerlist=[]
	count=0
	for input in config['Inputs']:
		if input['Location']=='I2C_GPIO':
			gpio=True
			#print "Have GPIO Users..."
		if input['Location']=='AnalogSync':
			analog=True
			#print "Have Analog Users..."
		if input['Location']=='System':
			system=True
			
	if gpio:
		gpio_users=io.read_inputs()
	if analog:
		analog_users=sync.get_analog_sync()
		#print "analog users:"+str(analog_users)

	for input in config['Inputs']:
		if input['Location']=='I2C_GPIO':
			bit=int(input['Associated_Port'])
			bank = bit/8
			bit = bit-1-(bank*8)
			enabled=False
			if (gpio_users[bank] &1<<bit) >0:	
				for logicItem in config['Logic']:
					if logicItem['Input']==input['Name']:
						#print logicItem['State']
						if logicItem['State']=='Enabled':
							count = count+1
							userlist.append(config['IO_List'].index(logicItem['Output']))
							enabled=True
				if enabled:
					mixerlist.append(input['Audio_Channel'])

	for input in config['Inputs']:
		if input['Location']=='AnalogSync':
			bit=int(input['Associated_Port'])
			#print "analog val:"+str(bit)
			enabled=False
			if (analog_users &1<<bit-1) >0:			
				for logicItem in config['Logic']:
					#print logicItem['Input']
					#print input['Name']
					if logicItem['Input']==input['Name']:
						if logicItem['State']=='Enabled':
							count = count+1
							userlist.append(config['IO_List'].index(logicItem['Output']))
							enabled=True
				if enabled:
					mixerlist.append(input['Audio_Channel'])
	#print userlist

	return count,userlist,map(int, mixerlist)
	
	


	
images =[]	
def update_image_list():	
	global images
	#get testcards list
	if(config["Display Settings"]["Testcards"]["Enabled"]):
		#show regular testcards
		directory = '/var/www/html/testcards/'
		files = os.listdir(directory)
		for img in files:
			if img.endswith('.jpg') or img.endswith('.JPG'):
				images.append(directory+img)
		
	#add metoffice datapoint weather images to list
	if(config["Display Settings"]["MetOfficeWx"]["Enabled"]):
		directory = '/var/www/html/MetOfficeWX/'
		files = os.listdir(directory)
		for img in files:
			if img.endswith('.png'):
				images.append(directory+img)
	
	#Display remote images
	for item in config["Remote Images"]["Links"]:
		if config["Remote Images"]["Links"][item]["Enabled"]:
			images.append("/var/www/html/RemoteImages/"+str(config["Remote Images"]["Links"][item]["link"].split('/')[-1]))
	
	
	directory = '/var/www/html/sonde/'
	files = os.listdir(directory)
	for img in files:
		if img.endswith('.png'):
			images.append(directory+img)
	
	#print images


imagepos=0
def carousel():
	#global timer_last
	global imagepos
	#print images
	if carousel_timer.elapsed():
		print "Cycling Carousel..."
		display.showtestcard(images[imagepos],True)
		
		if imagepos<len(images)-1:
			imagepos+=1
		else:
			imagepos=0






#OSD version
#osd.write(2,1,1,"text")

	

	
def update_audio_mixer(userlist,mixerlist,frompi):
	global mix
	#mixer.write(config['Audio_Squelch_Level'])
	#print config['Audio_Squelch_Level']

	#mixer.write(config['Audio_Master_Level'])
	#print config['Audio_Master_Level']

	#mixer.write(config['Audio_Channel_Level'])
	#print config['Audio_Channel_Level']
	
	#get sysop channel, add to list of inputs which are to be fed to both left and right
	dual=[]
	for item in config['Inputs']:
		if (item['Name']=="Sysop"):
			dual.append(int(item['Audio_Channel']))

	
	#mix inputs alternately to Left/Right output channels unless in dual list where they go to both
	mixLR=[0,0,0,0,0,0]
	n=0
	#print mixerlist
	#print dual
	for user in mixerlist:
		if(user in dual):	#input gets sent to both left and right, i.e Sysop
			mixLR[0]=mixLR[0] |  1 << (user-1)
			mixLR[1]=mixLR[1] |  1 << (user-1)
		else:
			if(n==0):
				mixLR[n]=mixLR[n] |  1 << (user-1)
				n=1
			else:
				mixLR[n]=mixLR[n] |  1 << (user-1)
				n=0
		mixLR[2]=mixLR[2] |  1 << (user-1)	#mono output (Analog tx)

	if frompi==True:
		#raspberry Left and Right output to both left and right main output
		mixLR[0]=mixLR[0] |  1 << 10 |  1 << 11 
		mixLR[1]=mixLR[1] |  1 << 10 |  1 << 11 
		mixLR[2]=mixLR[2] |  1 << 10 |  1 << 11 
		mixLR[3]=mixLR[2] |  1 << 10 |  1 << 11 
		mixLR[4]=mixLR[0] |  1 << 10 |  1 << 11 	#=ch0
		mixLR[5]=mixLR[1] |  1 << 10 |  1 << 11 	#=ch1
	else:
		mixLR[0]=mixLR[0] 
		mixLR[1]=mixLR[1] 
		mixLR[2]=mixLR[2] 
		mixLR[3]=mixLR[2]
		mixLR[4]=mixLR[0]	#=ch1
		mixLR[5]=mixLR[1]	#=ch2

	#2x 8-bit per output channel
	mix= [mixLR[5]>>8,mixLR[5]&0xff,mixLR[4]>>8,mixLR[4]&0xff,mixLR[3]>>8,mixLR[3]&0xff,mixLR[2]>>8,mixLR[2]&0xff,mixLR[1]>>8,mixLR[1]&0xff,mixLR[0]>>8,mixLR[0]&0xff]
	#mix= [0,0,0,0,0,0,mixLR[2]>>8,mixLR[2]&0xff,mixLR[1]>>8,mixLR[1]&0xff,mixLR[0]>>8,mixLR[0]&0xff]
	#print mix
	vals = config['Audio_Squelch_Level']+config['Audio_Master_Level']+config['Audio_Channel_Level']+mix
	#print vals
	#mixer.write(mix)
	mixer.write(vals)
	time.sleep(0.1)

	
	
def update_screen(num_users,userlist,k):
	print "Updating Screen....."+str(k)

	if k:
		print  "Userlist:" + str(userlist) + " K" 
		display.showtestcard("gb3km_k.jpg",False)	#no wipe
		enc.disable_osd_image(0)
		enc.disable_osd_image(1)
		videoswitch.select_single(CAROUSEL)

	else:
		if num_users==0:
			#print "Users:"+str(num_users)+ " Userlist:" + str(userlist) + " Carousel"
			enc.disable_osd_image(0)
			enc.disable_osd_image(1)
			videoswitch.select_single(CAROUSEL)


		if num_users==1:
			print  "One User:" + str(userlist) + " Fullscreen"
			videoswitch.select_single(userlist[0])


		if num_users>1:
			if num_users>4:
				print "Userlist:" + str(userlist) + " 9-Way Screen"
				videoswitch.select_nine(userlist,num_users)
			else:
				if num_users==2:	
					print "Userlist:" + str(userlist) + " Dual screen"
					videoswitch.select_dual(userlist,num_users)
					
				else:
					print "Userlist:" + str(userlist) + " 4-Way Screen"
					videoswitch.select_quad(userlist,num_users)
		#update_user_ident(userlist)


def set_analog_sync_active():
	active=0
	global config
	#print config['Inputs']
	for input in config['Inputs']:
		if input['Location']=='AnalogSync':
			active = active | int(input['Associated_Port'])
	sync.set_syncactive(active)
	print "Active Sync: "+str(active)



def init_audio_mixer():
	global mixer
	port = '/dev/AudioMixer'		#mapped from ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter, will only work if one attached, second will fail!
	f = open(port)
	attrs = termios.tcgetattr(f)
	attrs[2] = attrs[2] & ~termios.HUPCL
	termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
	f.close()
	mixer = serial.Serial(port, 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)	
	
	




#default state:
def setup():
	print "Setting up......."
	global lcd
	global Inet_access
	#comms_timer()
	lcd = pylcd.lcd(0x23, 1,2)

	#wait for network to be up
	n=0
	lcd.lcd_clear()
	while(n<60):
		lcd.lcd_puts("Wating for Ethernet..."+str(n),1,0)
		if is_interface_up("eth0"):
			lcd.lcd_clear()
			lcd.lcd_puts("Ethernet is online :-)",1,0)
			time.sleep(2)
			break
		else:
			time.sleep(2)
		n=n+1
	
	if debug==False:
		n=0
		lcd.lcd_clear()
		while(n<60):
			lcd.lcd_puts("Checking for router... :"+str(n),1,0)
			response = os.system("ping -c 1 -W 1 192.168.88.1 >/dev/null")
			time.sleep(1)
			if response==0:
				time.sleep(1)
				lcd.lcd_clear()
				lcd.lcd_puts("Router found :-)",1,0)
				time.sleep(2)
				break
			n=n+1
		if n==60:
			lcd.lcd_clear()
			lcd.lcd_puts("Router not found!!!",1,0)
			time.sleep(2)

		n=0
		lcd.lcd_clear()
		while(n<60):
			lcd.lcd_puts("Checking for Encoder... :"+str(n),1,0)
			response = os.system("ping -c 1 -W 1 192.168.88.249 >/dev/null")
			if response==0:
				time.sleep(1)
				lcd.lcd_clear()
				lcd.lcd_puts("Encoder found :-)",1,0)
				time.sleep(2)
				break
			n=n+1
		if n==60:
			lcd.lcd_clear()
			lcd.lcd_puts("Encoder not found!!!",1,0)
			time.sleep(2)

		n=0
		lcd.lcd_clear()
		while(n<60):
			lcd.lcd_puts("Checking for Pluto... :"+str(n),1,0)
			response = os.system("ping -c 1 -W 1 192.168.88.16 >/dev/null")
			if response==0:
				time.sleep(1)
				lcd.lcd_clear()
				lcd.lcd_puts("Pluto found :-)",1,0)
				time.sleep(2)
				break
			n=n+1
		if n==60:
			lcd.lcd_clear()
			lcd.lcd_puts("Pluto not found!!!",1,0)
			time.sleep(2)


		lcd.lcd_clear()
		lcd.lcd_puts("Rebooting ADALM Pluto",1,0)
		print "Sending reboot request to Pluto..."
		try:
			requests.post('http://192.168.88.16/pluto.php',{'reboot': ''})
		except:
			print "Error rebooting Pluto."
		time.sleep(4)	#pluto take a while to restart if already online
		lcd.lcd_clear()

		while(n<60):
			lcd.lcd_puts("Waiting for Pluto to Reboot... :"+str(n),1,0)
			response = os.system("ping -c 1 -W 1 192.168.88.16 >/dev/null")
			if response==0:
				time.sleep(1)
				lcd.lcd_clear()
				lcd.lcd_puts("Pluto found :-)",1,0)
				time.sleep(2)
				break
			n=n+1
		if n==60:
			lcd.lcd_clear()
			lcd.lcd_puts("Pluto not found!!!",1,0)
			time.sleep(2)

		
		#####################################################################
		## restart UDP on Encoder Box
		lcd.lcd_clear()
		lcd.lcd_puts("Configuring Encoder...",1,0)
		enc.set_streaming_source()		#set streaming params for 'sub stream' 1280x720, h264, 15fps
		enc.streaming("SD")
		time.sleep(1)
		enc.restartUDP()
		lcd.lcd_clear()
		lcd.lcd_puts("Starting Logic...",1,0)
		#####################################################################

		
		



def comms_timer():
	global comms485
	comms485.read_devices()

	for tmr in config["Timers"]:
		for n in range(comms485.devicecount):
			BeaconTx=False
			ActivityTx=False
			info = comms485.list_devices(n)
			if info != {}:	#if not empty
				name = info["INFO"].split(',')[0]
				#print name
				if tmr["Name"] == name :
					if tmr["Enabled"]=="True":
						weekday = int(time.strftime("%w"))
						for day in tmr["Days"].split(','):
							if int(day)==weekday:
								on = datetime.strptime(datetime.today().strftime("%Y-%m-%d "+tmr["BeaconOn"]),'%Y-%m-%d %H:%M')	
								off = datetime.strptime(datetime.today().strftime("%Y-%m-%d "+tmr["BeaconOff"]),'%Y-%m-%d %H:%M')
								if datetime.today() > on:
									if datetime.today() < off:
										#print "Tx On:"+name
										BeaconTx=True
									else:
										#print "Tx Off:"+name
										BeaconTx=False
								else:
									BeaconTx=False
									#print "Tx Off:"+name
								
								#Enable Activity Start
								if RepeaterInUse:
									on = datetime.strptime(datetime.today().strftime("%Y-%m-%d "+tmr["OperatingOn"]),'%Y-%m-%d %H:%M')	
									off = datetime.strptime(datetime.today().strftime("%Y-%m-%d "+tmr["OperatingOff"]),'%Y-%m-%d %H:%M')
									if datetime.today() > on:
										if datetime.today() < off:
											##print "Tx Off:"+name
											ActivityTx=True
										else:
											#print "Tx Off:"+name
											ActivityTx=False
									else:
										ActivityTx=False
										#print "Tx Off:"+name
								else:
										ActivityTx=False
					else:
						BeaconTx=False
					#update device
					if BeaconTx or ActivityTx:
						comms485.enable_output(n,4)
						print "Tx On:"+name
					else:
						comms485.disable_output(n,4)
						print "Tx Off:"+name
	#exit(0)


def check_config():
	global config
	global configtime
	
	#Check if web settings have chnaged and trigger restart sequence if it has
	if (os.stat('/var/www/html/io_config.json').st_ctime > configtime):
		json_file=open('/var/www/html/io_config.json')
		config = json.load(json_file)
		json_file.close()
		restart=True
		configtime= os.stat('/var/www/html/io_config.json').st_ctime
		print "Config file changed, re-loaded"
		display.showbanner("Config change detected...")
		
		set_Dir()					#io config
		set_analog_sync_active()	#sync config
		#update_audio_mixer(0,[])	#mixer config
		#usercount=0
		videoswitch.configure_modes(config["VideoSwitchSettings"]["mode2"],config["VideoSwitchSettings"]["mode4"],config["VideoSwitchSettings"]["default_QUAD"],config["VideoSwitchSettings"]["default_NINEWAY"],config["VideoSwitchSettings"]["pip_toggle_enabled"])
		#check_users(True)

		update_image_list()
		
	time.sleep(0.5)


def create_status():
	global analog_users
	global gpio_users
	global status

	status={}
	status["Sync"]=analog_users
	status["GPIO"]=gpio_users
	
	#print "Status........................................................"
	#print analog_users
	#print gpio_users
	remotes={}
	for n in range(comms485.devicecount):
		print "DC:"+str(n)
		info = comms485.list_devices(n)
		if info != {}:	#if not empty
			remotes[str(n)]=info
	status["Remote"]=remotes
	#print status
	UDP_socket.sendto(bytes(status), ("127.0.0.1", 9010))
	#json_file=open('/tmp/status',"w")
	#json_file.write(json.dumps(status))
	#json_file.close()
	#print "Status End...................................................."

	
				
	
def check_schedule():
	weatherpictime=0
	MetOfficeWXpictime=0
	global debug
	global lastuserlist
	logtime=0
	update=False
	
	

	while(True):
		if not debug:		#dont download every time during testing!
			#Check if it's time to grab new remote images
			if(time.time() - weatherpictime > 3600):
				print "Getting remote images..."
				#showbanner("Downloading Remote Images...")
				time.sleep(1)
				for item in config["Remote Images"]["Links"]:
					if config["Remote Images"]["Links"][item]["Enabled"]:
						#print config["Remote Images"]["Links"][item]
						file = config["Remote Images"]["Links"][item]["link"].split('/')[-1]
						#print 'wget --timeout 5 -q -O /var/www/html/Remote Images/%s %s'% (file, config["Remote Images"]["Links"][item]["link"])
						err = os.system('wget --timeout 5 -q -O /var/www/html/RemoteImages/%s %s'% (file, config["Remote Images"]["Links"][item]["link"]))
						if(err != 0):
							os.system('rm /var/www/html/RemoteImages/%s'% file)
							print "Error - "+config["Remote Images"]["Links"][item]["link"],err
				weatherpictime = time.time()
				
				#bodge for upper air maps on same timing
				print "getting sonde..."
				os.system('python /home/pi/logic/sonde/sonde.py')
				update=True

				#check internet
				Inet_Access=have_internet()
				

			#Check if it's time to grab met officde wx images 15min
			if(time.time() - MetOfficeWXpictime > 600):
				print "getting met wx..."
				display.showbanner("Downloading Remote Images...")
				time.sleep(1)
				os.system('python /home/pi/logic/wx/wx.py')
				MetOfficeWXpictime = time.time()
				update=True


				

			if update:
				print "Updating Image List..."
				update_image_list()
				print "Complete."
				update=False
			
			

		

		if(time.time() - logtime > 60):
			if usercount>0:
				#print "Log Users:"
				string =time.strftime("%d/%m/%Y,%H:%M:%S", time.localtime())
				for user in lastuserlist:
					for logicItem in config['Logic']:
						if user==config['IO_List'].index(logicItem['Output']):
							string=string+","
							string=string+logicItem['Input']
				string=string+"\n"
				#print string
				print "Logged."
				logfile = open('/var/www/html/log.txt','a')
				logfile.write(string)
				logfile.close()
			logtime=time.time()
		time.sleep(1)


def update_user_ident(userlist,pos):
	sd_width=1280
	sd_height=720
	hd_width=1920
	hd_height=1080
	string=""
	global useridentpos



	if len(userlist)>0:
		if len(userlist)==2 and videoswitch.mode2==1:	#toggle user list depending on who is full screen
			if not videoswitch.pip_toggle:
				userlist=userlist[1:] + userlist[:1]

		if len(userlist)==1 or (len(userlist)==2 and videoswitch.mode2==1):	#update with user in list pos zero
			for logicItem in config['Logic']:
				if userlist[0]==config['IO_List'].index(logicItem['Output']):
					string=logicItem['Input']
					break
			enc.create_osd_image(string,28)
			enc.upload_osd_image(1)
			enc.enable_osd_image(1,15,15,64)
			enc.create_osd_image(string,28)
			enc.upload_osd_image(0)
			enc.enable_osd_image(0,15,15,64)
		else:
			if len(userlist)>1 and len(userlist)<5:	#cycle around screen identifying stations
				pos=pos-1
				print "useridentpos="+str(pos)
				print userlist

		


				for logicItem in config['Logic']:
					if pos<len(userlist):
						if userlist[pos]==config['IO_List'].index(logicItem['Output']):
							string=logicItem['Input']
							if pos % 2 == 0:
								hdpos_x=0
								sdpos_x=0
							else:
								hdpos_x=hd_width/2
								sdpos_x=sd_width/2
							if pos>1:
								hdpos_y=hd_height/2-5
								sdpos_y=sd_height/2-5
							else:
								hdpos_y=0
								sdpos_y=0
							enc.create_osd_image(string,28)
							enc.disable_osd_image(1)
							enc.upload_osd_image(1)
							enc.enable_osd_image(1,15+sdpos_x,15+sdpos_y,64)
							enc.create_osd_image(string,28)
							enc.disable_osd_image(0)
							enc.upload_osd_image(0)
							enc.enable_osd_image(0,15+hdpos_x,15+hdpos_y,64)
							break
				

				#enc.disable_osd_image(0)
				#enc.disable_osd_image(1)
						

def check_users(force_update):
	global lastuserlist
	global usercount
	global mixerlist
	global osd_timer
	global user_ident_timer
	global useridentpos
	global RepeaterInUse
	global tx_hang_timer
	num,list,mixerlist=get_users()
	

	#add toggle for PIP mode to swap the pictures about


	if lastuserlist!=list:
		if num>0:
			RepeaterInUse=True
		else:
			RepeaterInUse=False
			tx_hang_timer.reset()
			
		if num<usercount:
			print "KKKKKK"
			update_screen(num,list,True)		#with k
			print "Starting timer"
			k_timer.reset()
			print "timer started"
			
			time.sleep(1)
			update_audio_mixer(list,mixerlist,True)
			os.system("echo 'k      ' | cw -s a -e -m  -w 18 -t 600 -v 35")	#send K audio
			update_audio_mixer(list,mixerlist,False)
			update_screen(num,list,False)	#Update screen
		else:
			if num>usercount:
				print "NEW USER...!"
				update_audio_mixer(list,mixerlist,True)
				update_screen(num,list,False)	#Update screen
				os.system("echo 'eee    ' | cw -s a -e -m  -w 18 -t 600 -v 35")	#send bips on new user
				update_audio_mixer(list,mixerlist,False)
		lastuserlist=list
		usercount=num




	if force_update:
		update_screen(num,list,False)	#Update screen		#different user but same number of users
		update_audio_mixer(list,mixerlist,False)
		print "forced update"

	if user_ident_timer.elapsed():
		if not osd_timer.is_started():
			osd_timer.start(5,num)
		else:
			if osd_timer.loop_elapsed():
				print "Ident..."
				update_user_ident(list,osd_timer.loop)
			if osd_timer.is_ended():
				user_ident_timer.reset()
				enc.disable_osd_image(0)
				enc.disable_osd_image(1)
	



def lcd_status():
	#display status on lcd screen
	global lcd_cycle
	global mix

	#if lcd_cycle==0:
	if debug==True:
		lcd.lcd_puts("*",2,33)
		lcd.lcd_puts("GB3KM",1,35)
	else:
		lcd.lcd_puts("GB3KM",1,35)

	if config["OperatingMode"][0]==0:
		lcd.lcd_puts("A",1,33)
	if config["OperatingMode"][0]==1:
		lcd.lcd_puts("M",1,33)
	lcd.lcd_puts(time.strftime("%H:%M", time.localtime()),2,35)

	#if lcd_cycle==0:
	string="Active:"
	if usercount>0:
		n=1
		for user in lastuserlist:
			for logicItem in config['Logic']:
				if user==config['IO_List'].index(logicItem['Output']):
					string=string+logicItem['Input']
			if n<usercount:
				string=string+"+"
			n=n+1	
	else:
		string = string+"Idle"

	if len(string)<33:
		string = string+ (" "*(33-len(string)))
	lcd.lcd_puts(string,1,0)


	if lcd_cycle==1:
		string = "L:"+LocalIPAddress
		string =string+ " R:"+RemoteIPAddress
		if len(string)<33:
			string = string+ (" "*(33-len(string)))
		lcd.lcd_puts(string,2,0)
	
	if lcd_cycle==2:
		string = "Internet Con:"+Inet_access
		if len(string)<33:
			string = string+ (" "*(33-len(string)))
		lcd.lcd_puts(string,2,0)
	
	if lcd_cycle==3:
		string = "MixL:"
		for i in range(10):
			if i>7:
				if mix[10]>>i-8 & 1:
					string = string+str(i+1)
					string=string+"+"
			else:
				if mix[11]>>i & 1:
					string = string+str(i+1)
					string=string+"+"
		#string=string+"PiL "
		string = string + " MixR:"
		for i in range(10):
			if i>7:
				if mix[8]>>i-8 & 1:
					string = string+str(i+1)
					string=string+"+"
			else:
				if mix[9]>>i & 1:
					string = string+str(i+1)
					string=string+"+"
		#string=string+"PiR"	
		if len(string)<33:
			string = string+ (" "*(33-len(string)))
		lcd.lcd_puts(string,2,0)

	lcd_cycle=lcd_cycle+1
	if lcd_cycle>3:
		lcd_cycle=0


def DTMFAction(command):
	if command:
		cmd = command.split(" ")
		if cmd[0]=="V":
			#set video switch to
			print "DTMF Set Video Switch:"+cmd[1]
			for Item in config['Logic']:
				if cmd[1]==Item['Input']:
					videoswitch.select_single(config['IO_List'].index(Item['Output']))
					#print "ch:"+str(config['IO_List'].index(Item['Output']))
			enc.create_osd_image(cmd[1],28)
			enc.upload_osd_image(1)
			enc.enable_osd_image(1,15,15,64)
			enc.create_osd_image(cmd[1],28)
			enc.upload_osd_image(0)
			enc.enable_osd_image(0,15,15,64)
		if cmd[0]=="M":
			print "Set OperatingMode:"+cmd[1]
			config['OperatingMode'] = [int(cmd[1])]
		if cmd[0]=="M2":
			print "Set 2-Op Mode:"+cmd[1]
			videoswitch.mode2 = int(cmd[1])
		if cmd[0]=="VM":
			print "Set 2/4 Mode:"+cmd[1]
			if cmd[1]=="2":
				videoswitch.set_dual()
			if cmd[1]=="4":
				videoswitch.set_quad()



def CheckTxStates():
	global LastRepeaterState
	if RepeaterInUse != LastRepeaterState:
		if RepeaterInUse:
			print "Repeater became active, switching on..."
			comms_timer()	##update tx etc.
			LastRepeaterState = RepeaterInUse
		else:
			if tx_hang_timer.elapsed():
				print "Repeater inactive, switching off..."
				comms_timer()	##update tx etc.
				LastRepeaterState = RepeaterInUse

		




# Timers
id_timer = timer_id()					#15min '900seconds
carousel_timer = repeating_timer(15)	#15sec
lcd_timer = repeating_timer(3)			#3sec
user_ident_timer = onetime_timer(60)	#60sec
k_timer = onetime_timer(2)				#
osd_timer = loop_timer(5,1)			#
pip_timer = repeating_timer(20)			#	
tx_hang_timer = onetime_timer(30)		# tx hang timer 5min 300

# General class inits
videoswitch = videoswitch()										#HDMI video switch
enc = encoder("192.168.88.249","m0dts","xxxxx")				#hdmi encoder
comms485 = Serial_485()											#serial for comms
display = display(display_type)									#display
io = IO()														#i2c io extender board	
sync = Sync()													#analog sync
osd = OSD()														#OSD MAX7456
dtmf = DTMF()
time.sleep(1)


setup()



# Timers
carousel_timer.interval=15	#15sec
k_timer.interval=2
lcd_timer.interval=8
user_ident_timer.interval=10
pip_timer.interval=config["VideoSwitchSettings"]["pip_toggle_time"]

#class init
enc.disable_osd_image(0)
enc.disable_osd_image(1)
videoswitch.select_single(CAROUSEL)
display.showtestcard("gb3km.jpg",False)

have_internet()

#init without full reload!
if not debug:
	configtime = os.stat('/var/www/html/io_config.json').st_ctime
	weatherpictime = time.time()
	MetOfficeWXpictime = time.time()


init_audio_mixer()

if not debug:
	display.animate()
	update_audio_mixer([],[],True)
	os.system("echo 'GB3KM     ' | cw -s a -e -m  -w 18 -t 600 -v 50")	#send ident cw

update_audio_mixer([],[],False)

update_image_list()


##########	thread for scheduler, update images etc.
scheduler_thread = threading.Thread(target=check_schedule, args=())
scheduler_thread.daemon = True
scheduler_thread.start()


# main loop, reads sync and updates video switch as required
while 1:
	if config["OperatingMode"][0]==0:	#Auto Mode
		check_config()
		carousel()

		if id_timer.elapsed():
			enc.disable_osd_image(0)
			enc.disable_osd_image(1)
			videoswitch.select_single(CAROUSEL)
			display.animate()
			update_audio_mixer([],[],True)
			os.system("echo 'GB3KM     ' | cw -s a -e -m  -w 18 -t 600 -v 50")	#send ident cw
			update_audio_mixer([],[],False)
			time.sleep(1.5)
			check_users(True)
		else:
			check_users(False)
			

		if lcd_timer.elapsed():
				lcd_status()

		if pip_timer.elapsed():
			videoswitch.toggle_pip()
			check_users(True)
		
		DTMFAction(dtmf.read_dtmf())

		CheckTxStates()
		create_status()



	if config["OperatingMode"][0]==1:		#hold mode
		check_config()
		if lcd_timer.elapsed():
			lcd_status()
		DTMFAction(dtmf.read_dtmf())
		print "."

	if config["OperatingMode"][0]==2:		#Manual Mode, still id's but does not change
		check_config()
		if lcd_timer.elapsed():
			lcd_status()
		DTMFAction(dtmf.read_dtmf())
		print "."


	time.sleep(0.5)