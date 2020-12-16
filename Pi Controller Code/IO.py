#!/usr/bin/python           # Sync detector value server
import time
import smbus


class IO:
	def __init__(self):
		self.bus = smbus.SMBus(1)	#i2c bus initialise port 1
		self.addr_base = 0x20	#address of first extender IC

		self.IODIRA = 0x00 # Pin direction register
		self.IODIRB = 0x01 # Pin direction register
		self.GPIOA  = 0x12 # Register for port A
		self.GPIOB  = 0x13 # Register for port B
		self.GPPUA  = 0xC  # Pullup reg port A
		self.GPPUB  = 0xD  # Pullup reg port B

		self.num_devices=3					#3x MCP23017
		self.direction=[0,0,0,255,255,255]	#default pin direction setting
		self.output=[0,0,0,0,0,0]			#default outputs

	def set_io_directions(self,direction):
		for device in range(self.num_devices):
			#print "Device"+str(device)
			for bank in range(2):
				#print bank
				if bank%2==0:	#if even
					self.bus.write_byte_data(self.addr_base+device,self.IODIRA,self.direction[device*2+bank])
				else:
					self.bus.write_byte_data(self.addr_base+device,self.IODIRB,self.direction[device*2+bank])				
		print "IO Directions:"+str(direction)

	def read_inputs(self):	
		n=0
		byte=0
		input=[]
		for device in range(self.num_devices):
			#print "Device Read:"+str(device)
			for bank in range(2):
				if bank%2==0:	#if even
					byte = self.bus.read_byte_data(self.addr_base+device,self.GPIOA)
				else:
					byte = self.bus.read_byte_data(self.addr_base+device,self.GPIOB)	
				n=n+1
				input.append(byte)
		return input


	def write_outputs(self,output):	
		n=0
		byte=0
		#print "out:"+str(output)
		for device in range(num_devices):
			for bank in range(2):
				if bank%2==0:	#if even
					self.bus.write_byte_data(self.addr_base+device,self.GPIOA,self.output[device*2+bank])
				else:
					self.bus.write_byte_data(self.addr_base+device,self.GPIOB,self.output[device*2+bank])	
				n=n+1

#io = IO()
#print io.read_inputs()
