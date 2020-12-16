#script to check powergood signal from pin7 on header
#shuts down the pi if powergood lost for more than 1 minute
#
#rob@m0dts.co.uk
#

import RPi.GPIO as GPIO
import time
import os


#GPIO pin wiring mode to header pin numbers
GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.IN)

print "Starting UPS monitor..."
time.sleep(30)
print "Waiting for power to fail!"

timer=0

while True:
	if GPIO.input(18)==0:
		timer=timer+1
		time.sleep(1)
	else:
		timer=0
		time.sleep(0.1)

	if timer>10:
		print "Shutting Down, power failure"
		os.system('halt')
		exit()
