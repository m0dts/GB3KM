import RPi.GPIO as GPIO
import time

class DTMF:
	def __init__(self):
		GPIO.setmode(GPIO.BOARD)

		self.D0=37
		self.D1=35
		self.D2=33
		self.D3=31
		self.DV=29

		GPIO.setup(self.DV, GPIO.IN)
		GPIO.setup(self.D0, GPIO.IN)
		GPIO.setup(self.D1, GPIO.IN)
		GPIO.setup(self.D2, GPIO.IN)
		GPIO.setup(self.D3, GPIO.IN)

		self.DTMF = ["D","1","2","3","4","5","6","7","8","9","0","*","#","A","B","C"]
		self.DTMFcount=0
		self.DTMFlasttime = time.time()
		self.DTMFcode =""
		self.code=""
		self.trigger=False
		GPIO.add_event_detect(self.DV, GPIO.RISING, callback=self.DTMFevent, bouncetime=10)
		self.validcodes={
			"80A":"V 1280A",
			"80D":"V 1280D",
			"65D":"V Ryde1",
			"75D":"V Ryde2",
			"002":"VM 2",
			"004":"VM 4",
			"000":"M 0",
			"111":"M 1",
			"220":"M2 0",
			"221":"M2 1"
		}

	def DTMFevent (self,pin):
		value = GPIO.input(self.D0) + (GPIO.input(self.D1)*2) + (GPIO.input(self.D2)*4) + (GPIO.input(self.D3)*8)	
		#print self.DTMF[value]
		if self.DTMF[value] == "*":
			self.DTMFlasttime = time.time()
		if time.time() - self.DTMFlasttime < 2:
			self.DTMFlasttime = time.time()
			self.DTMFcount +=1
			self.DTMFcode=self.DTMFcode+str(self.DTMF[value])
			if self.DTMF[value] == "#":
				self.DTMFcount = 0
				self.code=self.DTMFcode.replace("#","").replace("*","")
				self.trigger=True
				#print self.DTMFcode
				self.DTMFcode=""
		else:
			self.DTMFcount =0
			self.DTMFcode=""
			self.trigger=False

	def read_dtmf(self):
		if self.trigger:	
			self.trigger=False
			return self.process_code(self.code)

	def process_code(self,code):
		for c in self.validcodes:
			if c==code:
				return self.validcodes[c]


	
'''dtmf=DTMF()

while 1:
	time.sleep(0.1)
	x=dtmf.read_dtmf()
	if x:
		print x'''

