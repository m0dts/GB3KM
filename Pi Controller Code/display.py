import pygame
import PIL
from PIL import Image
import os
import random
import time
import math


class display:
    def __init__(self,display_type):
        if display_type == "composite":
            self.scrn_w = 720  # pygame screen size (framebuffer)
            self.scrn_h = 576
            self.lborder = 30 
            self.rborder = 20
            self.tborder = 20
            self.bborder = 20
            self.scroll=self.scrn_w/48
            os.system('sudo fbset -g '+str(self.scrn_w)+' '+str(self.scrn_h)+' '+str(self.scrn_w)+' '+str(self.scrn_h)+' 16')
        else:
            self.scrn_w = 1280
            self.scrn_h = 720
            self.lborder = 0
            self.rborder = 0
            self.tborder = 0
            self.bborder = 0
            self.scroll=(self.scrn_w/48)*2
            os.system('sudo fbset -g '+str(self.scrn_w)+' '+str(self.scrn_h)+' '+str(self.scrn_w)+' '+str(self.scrn_h)+' 16')

        os.system('sudo fbset')

        pygame.init()
        print "Press Ctrl-C to continue if loaded previously..!"
        self.screen = pygame.display.init()
        self.screen = pygame.display.set_mode([self.scrn_w,self.scrn_h])  #open framebuffer, needs to be same size as framebuffer, set in /boot/config.txt to 720x576
        pygame.mouse.set_visible(0)
        pygame.font.init()
        print "Screen Initialised..."


    #Info banner
    def showbanner(self,text):
        self.font=pygame.font.SysFont("Sans",22)
        text=self.font.render(text, 1,(255,255,255))
        pygame.draw.rect(self.screen, (200,50,50), ((self.scrn_w/2)-(text.get_width()/2),(self.scrn_h/2)-10,text.get_width()+20,text.get_height()+20),0)
        self.screen.blit(text, ((self.scrn_w/2)-(text.get_width()/2)+10,self.scrn_h/2))
        pygame.display.flip()			#update screen



        
    def showtestcard(self,testcard,wipe):	#wipe is bool
        pygame.draw.rect(self.screen, (0, 0, 0), [0, 0, self.lborder, self.scrn_h])  # fix edge
        #print testcard
        if os.path.isfile(testcard):		#double check testcard is still there!
            try:
                bg = pygame.image.load(testcard)       #load page layout
                imagerect = bg.get_rect()               #get size of image
                basewidth = self.scrn_w-self.lborder-self.rborder
                img = Image.open(testcard).convert('RGB')
                vsize = self.scrn_h-self.tborder-self.bborder
                img = img.resize((basewidth,vsize), PIL.Image.ANTIALIAS)
                bg = pygame.image.fromstring(img.tobytes(), img.size, 'RGB')

                if wipe:
                    r=random.randint(0,1)
                    if r==1:
                        for n in reversed(range(self.lborder,self.scrn_w,self.scroll)):
                            self.screen.blit(bg,(n,self.tborder))
                            pygame.display.update()                   	#update screen
                    else:
                        for n in range(-self.scrn_w,self.lborder,self.scroll):
                            self.screen.blit(bg,(n,self.tborder))
                            pygame.display.update()                   	#update screen
                        self.screen.blit(bg,(self.lborder,self.tborder))
                        pygame.display.update()                   	#update screen
                else:
                    self.screen.blit(bg,(self.lborder,self.tborder))    		#display page layout image
                    pygame.display.update()

                pygame.draw.rect(self.screen, (0,0,0), [self.scrn_w-self.rborder, 0, self.rborder, self.scrn_h])	#fix edge
                pygame.display.update()
            except:
                print "Erro loading testcard"
                pass












    #animation
    

    def straight_plot(self,startx,starty,direction,length,colour):
        global x,y
        for n in range(int(length)-1):
            if direction=='right':
                pygame.draw.line(self.screen, colour, (startx+n,starty), (startx+n+1,starty), 3)
                x+=1
            if direction=='left':
                pygame.draw.line(self.screen, colour, (startx-n,starty), (startx-n-1,starty), 3)
                x-=1
            if direction=='up':
                pygame.draw.line(self.screen, colour, (startx,starty-n), (startx,starty-n-1), 3)
                y-=1
            if direction=='down':
                pygame.draw.line(self.screen, colour, (startx,starty+n), (startx,starty+n+1), 3)
                y+=1
        pygame.display.update()
        time.sleep(0.1)

    def sine(self,colour,cycles,amplitude):
        global x,y
        lasty=y
        for n in range(cycles*10+1):
            _y = amplitude*50*math.sin(math.radians(n*36))   
            pygame.draw.line(self.screen, colour, (x,lasty), (x+1,y+_y), 3)
            x+=1
            lasty=y+_y
            pygame.display.update()
        #time.sleep(0.1)

    def animate(self):  # wipe is bool
        global x,y
        x=0
        y=0
        sync=0.28/3
        # if not wipe:
        self.font = pygame.font.SysFont("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", 192)
        self.screen.fill((0))		#left,top,width,height
        refline=self.scrn_h-(self.scrn_h/3)

        
        x=0
        y=refline

        self.straight_plot(x,y,'right',0.05*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'down',sync*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'right',0.03*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'up',sync*self.scrn_w,(128,128,128))

        self.straight_plot(x,y,'right',0.05*self.scrn_w,(128,128,128))
        self.sine((255,128,128),4,1)
        self.straight_plot(x,y,'right',0.05*self.scrn_w,(128,128,128))

        self.straight_plot(x,y,'up',0.02*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'right',0.02*self.scrn_w,(128,128,128))

        self.straight_plot(x,y,'up',0.25*self.scrn_w,(128,128,128))


        self.straight_plot(x,y,'right',0.08*self.scrn_w,(128,128,128))    #white

        self.sine((255,255,0),10,2)  #yel
        self.straight_plot(x,y,'down',0.035*self.scrn_w,(255,255,0))

        text = self.font.render("G", True, (255,255,0))
        self.screen.blit(text,(x-(text.get_width()//2),refline))
        pygame.display.flip()
        self.sine((64,255,255),10,2) #cyan
        self.straight_plot(x,y,'down',0.035*self.scrn_w,(64,255,255))

        text = self.font.render("B", True, (64,255,255))
        self.screen.blit(text,(x-(text.get_width()//2),refline))
        pygame.display.flip()
        self.sine((0,255,0),10,2)    #green
        self.straight_plot(x,y,'down',0.035*self.scrn_w,(0,255,0))

        text = self.font.render("3", True, (0,255,0))
        self.screen.blit(text,(x-(text.get_width()//2),refline))
        pygame.display.flip()
        self.sine((255,0,255),10,2)  #magenta
        self.straight_plot(x,y,'down',0.035*self.scrn_w,(255,0,255))

        text = self.font.render("K", True, (255,0,255))
        self.screen.blit(text,(x-(text.get_width()//2),refline))
        pygame.display.flip()
        self.sine((255,0,0),10,2)    #red
        self.straight_plot(x,y,'down',0.035*self.scrn_w,(255,0,0))

        text = self.font.render("M", True, (255,0,0))
        self.screen.blit(text,(x-(text.get_width()//2),refline))
        pygame.display.flip()
        self.sine((0,0,255),10,2)    #blue
        self.straight_plot(x,y,'down',0.08*self.scrn_w,(0,0,255))

        self.straight_plot(x,y,'right',0.08*self.scrn_w,(128,128,128))        #black
        self.straight_plot(x,y,'down',0.02*self.scrn_w,(128,128,128))

        self.straight_plot(x,y,'right',0.07*self.scrn_w,(128,128,128))
        #pygame.draw.rect(self.screen, (0, 0, 0), [0, 0, lborder, self.scrn_h])  # fix edge

        self.straight_plot(x,y,'down',sync*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'right',0.03*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'up',sync*self.scrn_w,(128,128,128))
        self.straight_plot(x,y,'right',0.1*self.scrn_w,(128,128,128))
        #pygame.draw.rect(self.screen, (0,0,0), [self.scrn_w-rborder, 0, rborder, self.scrn_h])	#fix edge


