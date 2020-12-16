#!/usr/bin/python           # Sync detector value server

import thread
import threading
import time
import RPi.GPIO as GPIO




class Sync:
	def __init__(self):

		self.lock = threading.Lock()
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(False)
		self.A=11
		self.B=13
		self.C=15
		self.DET=7
		GPIO.setup(self.A, GPIO.OUT)
		GPIO.setup(self.B, GPIO.OUT)
		GPIO.setup(self.C, GPIO.OUT)
		GPIO.setup(self.DET,GPIO.IN)
		self.running=True
		self.syncval =0
		self.syncactive=255	#default all active, used to check which inputs to check, faster if less are active
		self.sync_averages=7
		self.sync_threshold=1
		self.sync_avg=[0,0,0,0,0,0,0,0]
		threading.Thread(target=self.read_sync_values).start()
		#thread.start_new_thread(self.read_sync_values,())

	def stop(self):
		self.running=False

	def set_syncactive(self,val):
		self.syncactive=val

	def get_analog_sync(self):
		return self.syncval

	def read_sync_values(self):
		while self.running:
			val=0
			for channel in range(8):
				if self.syncactive>>channel&1:
					#print channel
					GPIO.output(self.A,channel&1)
					GPIO.output(self.B,channel>>1&1)
					GPIO.output(self.C,channel>>2&1)
					time.sleep(0.15)
					if 1-GPIO.input(self.DET):						#if sync true
						if self.sync_avg[channel]<self.sync_averages:		#if averge value less than averages to take
							self.sync_avg[channel]+=1				#add 1 to sync avg value
					else:
						if self.sync_avg[channel]>0:
							self.sync_avg[channel]-=1
					time.sleep(0.1)

			for channel in range(8):							#create sync byte
				if self.syncactive>>channel&1:
					if self.sync_avg[channel]>self.sync_threshold:
						val|=1<<channel
						
			self.lock.acquire()
			self.syncval=val
			self.lock.release()
			#print self.syncval

		
#GPIO.input(DET)


#sync=Sync()
#sync.get_analog_sync()
#sync.stop()
