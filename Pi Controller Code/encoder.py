#	Python utils to remote control BrovoTech h265/h265 HDMI Encoder
# 	Work in progress...
#   rob@m0dts.co.uk 
# 	29/10/2020
# 
# 	apt-get install python-pil python-xmltodict python-requests
# 
# 

import requests
import time
from PIL import Image,ImageDraw,ImageFont
import xmltodict
from io import BytesIO

class encoder:
	def __init__(self,_encoderIP,_streamname,_streamkey):
		self.encoderIP = _encoderIP
		self.xml_headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
		self.fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
		self.streamname = _streamname
		self.streamkey = _streamkey
		self.streamurl="rtmp://rtmp.batc.org.uk/live/"
		self.imagenum=0
		self.nettimeout=10
		self.tempimage=""

	##################
	#
	#	UDP OUTPUT RESTART - can be handy at power up if pluto does not start transmitting
	#

	def restartUDP(self):
		try:
			xml= requests.post('http://'+self.encoderIP+'/action/get?subject=multicast', auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		xmldict= xmltodict.parse(xml)
		xmldict['response']['multicast']['mcast'][0]['active']="0"
		xml_data = xmltodict.unparse(xmldict)
		try:
			requests.post('http://'+self.encoderIP+'/action/set?subject=multicast', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		time.sleep(2)
		xmldict['response']['multicast']['mcast'][0]['active']="1"
		xml_data = xmltodict.unparse(xmldict)
		try:
			requests.post('http://'+self.encoderIP+'/action/set?subject=multicast', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
	#
	#
	#	
	##########	


	##################
	#
	#	RTMP STREAMING
	#
	def streaming(self,state):
		
		try:
			xml= requests.post('http://'+self.encoderIP+'/action/get?subject=rtmp', auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		#print xml
		xmldict= xmltodict.parse(xml)

		if state=="OFF":
			xmldict['response']['rtmp']['push'][0]['active']="0"
			xmldict['response']['rtmp']['push'][1]['active']="0"
			xmldict['response']['rtmp']['push'][2]['active']="0"
			xmldict['response']['rtmp']['url']=self.streamurl+self.streamname+"-"+self.streamkey
			xml_data = xmltodict.unparse(xmldict)
			try:
				requests.post('http://'+self.encoderIP+'/action/set?subject=rtmp', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
			except:
				print "Error Setting Streaming off..."

		if state=="SD":
			xmldict['response']['rtmp']['push'][0]['active']="0"
			xmldict['response']['rtmp']['push'][1]['active']="1"
			xmldict['response']['rtmp']['push'][2]['active']="0"
			xmldict['response']['rtmp']['push'][1]['url']=self.streamurl+self.streamname+"-"+self.streamkey
			xml_data = xmltodict.unparse(xmldict)
			#print xml_data
			try:
				requests.post('http://'+self.encoderIP+'/action/set?subject=rtmp', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
			except:
				print "Error Setting Streaming sd..."

		if state=="HD":
			xmldict['response']['rtmp']['push'][0]['active']="1"
			xmldict['response']['rtmp']['push'][1]['active']="0"
			xmldict['response']['rtmp']['push'][2]['active']="0"
			xmldict['response']['rtmp']['push'][0]['url']=self.streamurl+self.streamname+"-"+self.streamkey
			xml_data = xmltodict.unparse(xmldict)
			try:
				requests.post('http://'+self.encoderIP+'/action/set?subject=rtmp', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
			except:
				print "Error Setting Streaming hd..."


	def set_streaming_source(self):
		try:
			xml= requests.post('http://'+self.encoderIP+'/action/get?subject=videoenc&stream=1', headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		#print xml
		xmldict= xmltodict.parse(xml)
		xmldict['response']['videoenc']['codec']="0"	#h264
		xmldict['response']['videoenc']['resolution']="1280x720"
		xmldict['response']['videoenc']['framerate']="15"
		xmldict['response']['videoenc']['keygop']="30"
		xmldict['response']['videoenc']['rc']="0"	#vbr
		xmldict['response']['videoenc']['bitrate']="400"
		#xmldict['response']['videoenc']['smartenc']="0"	#what is this?
		xml_data = xmltodict.unparse(xmldict)
		xml_data
		try:
			requests.post('http://'+self.encoderIP+'/action/set?subject=videoenc&stream=1', data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			print "Error Setting Streaming source..."
	#
	#
	#	
	##########





	#####################
	#
	#	Image OSD functions
	#	An image is better quality than the text over built in but does not support transparency
	#
	def create_osd_image(self,string,fontsize):
		self.imagenum=self.imagenum+1		#different filename initiates refresh of image automatically
		startsize=fontsize
		font = ImageFont.truetype(self.fontfile, startsize)
		(width, height), (offset_x, offset_y)=font.font.getsize(string)
		#print width,height,offset_y
		text = string
		image = Image.new('RGB', (width+8,height+8), (50,50,50) )
		draw = ImageDraw.Draw(image)

		xpos=(width/2)
		ypos=(height/2)
		draw.text((4,4-offset_y),text, fill="white",font=font)
		try:
			self.tempimage= BytesIO()
			image.save(self.tempimage,format="JPEG", quality=95)
			self.tempimage.name="image"+str(self.imagenum)+".jpg"
			self.tempimage.seek(0)
		except:
			return "Error saving file"

	def upload_osd_image(self,channel):
		files = {'file': ("image"+str(self.imagenum)+".jpg", self.tempimage.read(), 'image/jpg')}
		#self.tempimage.seek(0)
		try:
			requests.post('http://'+self.encoderIP+'/action/upload?file=osdpic'+str(channel),files=files,auth=('admin', '12345'),timeout=self.nettimeout)
		except:
			return "Error with request"

	def enable_osd_image(self,channel,locx,locy,opacity):
		try:
			xml= requests.post('http://'+self.encoderIP+'/action/get?subject=osd&stream='+str(channel), auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		#print xml
		xmldict= xmltodict.parse(xml)
		xmldict['response']['osd']['picture']['active']="1"
		xmldict['response']['osd']['picture']['xpos']=str(locx)
		xmldict['response']['osd']['picture']['ypos']=str(locy)
		xmldict['response']['osd']['picture']['transparent']=str(opacity)
		xml_data = xmltodict.unparse(xmldict)
		try:
			requests.post('http://'+self.encoderIP+'/action/set?subject=osd&stream='+str(channel), data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"


	def disable_osd_image(self,channel):
		try:
			xml= requests.post('http://'+self.encoderIP+'/action/get?subject=osd&stream='+str(channel), auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
		#print xml
		xmldict= xmltodict.parse(xml)
		xmldict['response']['osd']['picture']['active']="0"
		xml_data = xmltodict.unparse(xmldict)
		try:
			requests.post('http://'+self.encoderIP+'/action/set?subject=osd&stream='+str(channel), data=xml_data, headers=self.xml_headers, auth=('admin', '12345'),timeout=self.nettimeout).text
		except:
			return "Error with request"
	#
	#
	#
	#######################
