#!/usr/bin/python           # Sync detector value server
import time
import spidev



class OSD:
	def __init__(self):
		self.spi = spidev.SpiDev()
		self.spi.open(0, 0)
		self.spi.max_speed_hz=(500000)
		time.sleep(0.001)

		#GPIO SPI speed
		self.delay = 0.00001

		#list of charachter map in MAX7456 memory, used for ASCII lookup later
		self.list = [" ","1","2","3","4","5","6","7","8","9","0","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","(",")",".","?",";",":",",","'","/",'"',"-","'"]



	#Read register from address
	def readbyte(self,addr):
		response = self.spi.xfer([addr,0])	#send second 8 clock cycles to allow for response!
		return response[1]

		
	#Turn on OSD
	def init(self):
		#set VM0 register: PAL, Auto Sync, OSD Enable, Immediate display, NO Reset, Buffer Enable = 0x48
		self.spi.xfer([0x00,0x48])
		
		#read VM1 reg, adjust background brightness level bits
		level=1	#black #0-7 range for 0-49% white level
		self.spi.xfer([0x01,(self.readbyte(0x81)&0x8f)|level<<4])
		
		print self.readbyte(0x84)

	#Clear all charachters from screen
	def clear(self):
		self.spi.xfer([0x04,4])	#clear display memory

	#Write test to screen at position x,y with or without black background
	def write(self,text,x,y,background):	# "TEST",0,1,1 = write TEST at start of decond row with black background 
		#set background bit of DMM Register
		self.spi.xfer([0x04,self.readbyte(0x84)&~32 | background<<5])
		
		#Write characters to display memory
		pos =1+x+(30*(y+1))
		
		for chr in text:
			self.spi.xfer([0x05,pos >> 8])#Upper bit of position register
			self.spi.xfer([0x06,pos])
			self.spi.xfer([0x07,self.list.index(chr)])
			pos += 1
			if pos > 480:
				pos = 0

	#print readbyte(0x84)

	#OSDinit()
	#OSDclear()
	#OSDwrite("M0DTS ROB IO94IL",0,0,0)
	#OSDwrite("Listen 144.750MHz",0,14,0)

#osd=OSD()
#print osd.readbyte(0x84)
#osd.init()
#osd.clear()
#osd.write("M0DTS ROB IO94IL",0,0,0)