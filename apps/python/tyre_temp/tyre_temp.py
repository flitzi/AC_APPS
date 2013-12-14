################################################################################
# Danny Giusa Tyre Temperatures
# danny(dot)giusa(at)gmail(dot)com
# V1.2, 06.12.2013, AC Early Access 0.3.0
# 
# This little app provides informations about the state of your
# tyre like temperature, pressure and level of dirt
#
# Changelog:
#
# 1.0 
# - restructure of the techpreview app
# - added level of dirt with raising bar on tyrebar
#
# 1.1
# - added max temps and psi recording
# - rearrange dirtbars and value
#
# 1.2
# - added max values
# - fixed that under 25C drawn tyres disappear
# - using hue of HSV color wheel for temperature coloring (flitzi)
# - variables for optimal temperature and temperature range (flitzi)
# - added spinner for adjusting the optimal temperature while in the car (flitzi)
# - new alignment for the ui
#
# 1.2.1
# - saving and loading optimal tyre temperature per car in C:/Users/[YourUserName]/AC_tyre_temp/ (flitzi)
# - added variable for showing/hiding optimal temperature spinner (flitzi)
#
# 1.2.2
# - only write optimal tyre temperature when changed (flitzi)
#
################################################################################

import string
import math
import ac
import acsys
import os.path
import struct                          # for converting from bytes to useful data
import mmap                            # for reading shared memory

###directory for storing ini files, home("~") is C:/Users/[YourUserName]
from os.path import expanduser
inidir = expanduser("~") + "/AC_tyre_temp/"

###valid file name characters
validFilenameChars = "-_() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

TYREINFO = 0
###appsize
x_app_size = 300
y_app_size = 195
###startingpoint of first label
x_start = 17
y_start = 40
###spaces from left to right label/tyre and upper and bottom
x_space = 215
y_space = 75
###spaces for drawn tyre 
x_tyre_position = x_start + 53 
y_tyre_position = y_start + 5
###spaces for drawn tyre from left to right
x_tyre_space = 80
x_tyredirt_space = 3
###settings for drawn tyre
w_tyre = 23
h_tyre = 50
###settings for offset of drawn tyredirt
w_tyredirt = w_tyre -6


################## CHANGE BACKROUND HERE ################## 
background = 0
################## CHANGE BACKROUND HERE ##################

###d_optimal_temp is displayed as green
###d_optimal_temp - temp_rage / 2 is displayed as blue
###d_optimal_temp + temp_rage / 2 is displayed as red
###if the optimal tyre temperature is set to 100 and the temperature range is 80 then 60 is displayed blue, 100 green and 140 red
###the optimal temperature can be adjusted using the spinner
d_optimal_temp = 100 
temp_range = 80 

###whether optimal temperature spinner is shown, 0=not shown, 1=shown
show_optimal_spinner = 1

class Tyre_Info:  

  def __init__(self, app, x, y):
    x_pressure = x
    x_dirt = x_pressure
    x_maxt = x + 80
    x_maxp = x_maxt
    
    y_pressure = y + 20
    y_dirt = y_pressure + 20
    y_maxt = y + 8
    y_maxp = y_maxt + 20
    
    self.maxtFL = 0
    self.maxtFR = 0
    self.maxtRL = 0
    self.maxtRR = 0
    
    self.maxpFL = 0
    self.maxpFR = 0
    self.maxpRL = 0
    self.maxpRR = 0
    
    ##initialize labels
    
    self.tFLValue = ac.addLabel(app, "temp fl")
    self.tFRValue = ac.addLabel(app, "temp fr")
    self.tRLValue = ac.addLabel(app, "temp rl")
    self.tRRValue = ac.addLabel(app, "temp rr")
    self.pFLValue = ac.addLabel(app, "psi fl")
    self.pFRValue = ac.addLabel(app, "psi fr")
    self.pRLValue = ac.addLabel(app, "psi rl")
    self.pRRValue = ac.addLabel(app, "psi rr")
    self.dFLValue = ac.addLabel(app, "dirt fl")
    self.dFRValue = ac.addLabel(app, "dirt fr")
    self.dRLValue = ac.addLabel(app, "dirt rl")
    self.dRRValue = ac.addLabel(app, "dirt rr")
    self.maxFont = ac.addLabel(app, "Max")
    self.maxtFont = ac.addLabel(app, "C")
    self.maxpFont = ac.addLabel(app, "psi")
    self.maxtFontBottom = ac.addLabel(app, "C")
    self.maxpFontBottom = ac.addLabel(app, "psi")
    self.maxtFLValue = ac.addLabel(app, "maxtemp fl")
    self.maxtFRValue = ac.addLabel(app, "maxtemp fr")
    self.maxtRLValue = ac.addLabel(app, "maxtemp rl")
    self.maxtRRValue = ac.addLabel(app, "maxtemp rr")
    self.maxpFLValue = ac.addLabel(app, "maxpress fl")
    self.maxpFRValue = ac.addLabel(app, "maxpress fr")
    self.maxpRLValue = ac.addLabel(app, "maxpress rl")
    self.maxpRRValue = ac.addLabel(app, "maxpress rr")
    
    ##set label positions
    
    ac.setPosition(self.tFLValue, x - 152, y)
    ac.setPosition(self.tFRValue, x + x_space, y)
    ac.setPosition(self.tRLValue, x - 152, y + y_space)
    ac.setPosition(self.tRRValue, x + x_space, y + y_space)
    ac.setPosition(self.pFLValue, x_pressure - 152, y_pressure)
    ac.setPosition(self.pFRValue, x_pressure + x_space, y_pressure)
    ac.setPosition(self.pRLValue, x_pressure - 152, y_pressure + y_space)
    ac.setPosition(self.pRRValue, x_pressure + x_space, y_pressure + y_space)
    ac.setPosition(self.dFLValue, x_dirt - 152, y_dirt)
    ac.setPosition(self.dFRValue, x_dirt + x_space, y_dirt)
    ac.setPosition(self.dRLValue, x_dirt - 152, y_dirt + y_space)
    ac.setPosition(self.dRRValue, x_dirt + x_space, y_dirt + y_space)
    ac.setPosition(self.maxFont, 137, 28)
    ac.setPosition(self.maxtFont, 145, 48)
    ac.setPosition(self.maxpFont, 140, 68)
    ac.setPosition(self.maxtFontBottom, 145, 123)
    ac.setPosition(self.maxpFontBottom, 140, 143)
    ac.setPosition(self.maxtFLValue, x_maxt, y_maxt)
    ac.setPosition(self.maxtFRValue, x_maxt - 96, y_maxt)
    ac.setPosition(self.maxtRLValue, x_maxt, y_maxt + y_space)
    ac.setPosition(self.maxtRRValue, x_maxt - 96, y_maxt + y_space)
    ac.setPosition(self.maxpFLValue, x_maxp, y_maxp)
    ac.setPosition(self.maxpFRValue, x_maxp - 96, y_maxp)
    ac.setPosition(self.maxpRLValue, x_maxp, y_maxp + y_space)
    ac.setPosition(self.maxpRRValue, x_maxp - 96, y_maxp + y_space)
    
    ##set label alignments
    
    ac.setFontAlignment(self.tFLValue, "right")
    ac.setFontAlignment(self.tRLValue, "right")
    ac.setFontAlignment(self.pFLValue, "right")
    ac.setFontAlignment(self.pRLValue, "right")
    ac.setFontAlignment(self.dFLValue, "right")
    ac.setFontAlignment(self.dRLValue, "right")
    ac.setFontAlignment(self.maxtFLValue, "left")    
    ac.setFontAlignment(self.maxtFRValue, "right")
    ac.setFontAlignment(self.maxtRLValue, "left")
    ac.setFontAlignment(self.maxtRRValue, "right")
    ac.setFontAlignment(self.maxpFLValue, "left")
    ac.setFontAlignment(self.maxpFRValue, "right")
    ac.setFontAlignment(self.maxpRLValue, "left")
    ac.setFontAlignment(self.maxpRRValue, "right")
    
    ##set font size
    
    ac.setFontSize(self.maxFont, 12)
    ac.setFontSize(self.maxtFont, 12)
    ac.setFontSize(self.maxpFont, 12)
    ac.setFontSize(self.maxtFontBottom, 12)
    ac.setFontSize(self.maxpFontBottom, 12)
    ac.setFontSize(self.maxtFLValue, 12)
    ac.setFontSize(self.maxtFRValue, 12)  
    ac.setFontSize(self.maxtRLValue, 12)
    ac.setFontSize(self.maxtRRValue, 12)
    ac.setFontSize(self.maxpFLValue, 12)
    ac.setFontSize(self.maxpFRValue, 12)
    ac.setFontSize(self.maxpRLValue, 12)
    ac.setFontSize(self.maxpRRValue, 12)
    
  def setTemp(self, tFL, tFR, tRL, tRR):
    ac.setText(self.tFLValue, "{0} C".format(round(tFL)))
    ac.setText(self.tFRValue, "{0} C".format(round(tFR)))
    ac.setText(self.tRLValue, "{0} C".format(round(tRL)))
    ac.setText(self.tRRValue, "{0} C".format(round(tRR)))
  
  def setPressure(self, pFL, pFR, pRL, pRR):
    ac.setText(self.pFLValue, "{0} psi".format(round(pFL)))
    ac.setText(self.pFRValue, "{0} psi".format(round(pFR)))
    ac.setText(self.pRLValue, "{0} psi".format(round(pRL)))
    ac.setText(self.pRRValue, "{0} psi".format(round(pRR)))
  
  def setDirt(self, dFL, dFR, dRL, dRR):
    ac.setText(self.dFLValue, "{0}%".format(round(dFL*20)))
    ac.setText(self.dFRValue, "{0}%".format(round(dFR*20)))
    ac.setText(self.dRLValue, "{0}%".format(round(dRL*20)))
    ac.setText(self.dRRValue, "{0}%".format(round(dRR*20)))
  
  def setWear(self, wFL, wFR, wRL, wRR):
    ac.setText(self.dFLValue, "{0}%".format(round(wFL)))
    ac.setText(self.dFRValue, "{0}%".format(round(wFR)))
    ac.setText(self.dRLValue, "{0}%".format(round(wRL)))
    ac.setText(self.dRRValue, "{0}%".format(round(wRR)))
  
  def setMaxT(self, tFL, tFR, tRL, tRR):
    if self.maxtFL < tFL:
      self.maxtFL = tFL
      ac.setText(self.maxtFLValue, "{0}".format(round(self.maxtFL)))
    if self.maxtFR < tFR:
      self.maxtFR = tFR
      ac.setText(self.maxtFRValue, "{0}".format(round(self.maxtFR)))
    if self.maxtRL < tRL:
      self.maxtRL = tRL
      ac.setText(self.maxtRLValue, "{0}".format(round(self.maxtRL)))
    if self.maxtRR < tRR:
      self.maxtRR = tRR
      ac.setText(self.maxtRRValue, "{0}".format(round(self.maxtRR)))

  def setMaxP(self, pFL, pFR, pRL, pRR):
    if self.maxpFL < pFL:
      self.maxpFL = pFL
      ac.setText(self.maxpFLValue, "{0}".format(round(self.maxpFL)))
    if self.maxpFR < pFR:
      self.maxpFR = pFR
      ac.setText(self.maxpFRValue, "{0}".format(round(self.maxpFR)))
    if self.maxpRL < pRL:
      self.maxpRL = pRL
      ac.setText(self.maxpRLValue, "{0}".format(round(self.maxpRL)))
    if self.maxpRR < pRR:
      self.maxpRR = pRR
      ac.setText(self.maxpRRValue, "{0}".format(round(self.maxpRR)))

def acMain(ac_version):
  global TYREINFO
  appWindow = ac.newApp("Tyre Temperatures")
  ac.drawBackground(appWindow, background)  
  ac.drawBorder(appWindow, background)
  ac.setBackgroundOpacity(appWindow, background)
  ac.setSize(appWindow, x_app_size, y_app_size)
  TYREINFO = Tyre_Info(appWindow, x_start, y_start)
  ac.addRenderCallback(appWindow, onFormRender)
  
  TYREINFO.optimal_temp = d_optimal_temp
  TYREINFO.carinifilepath = inidir + getValidFileName(ac.getCarName(0)) + ".ini"
  TYREINFO.needwriteini = 1
  
  if os.path.exists(TYREINFO.carinifilepath):
    f = open(TYREINFO.carinifilepath, "r")
    TYREINFO.optimal_temp = int(f.readline()[8:])
    f.close()
    TYREINFO.needwriteini = 0
  
  if show_optimal_spinner == 1:
    optimal_spinner_id = ac.addSpinner(appWindow, "optimal")
    ac.setPosition(optimal_spinner_id, x_start, y_start + 200) 
    ac.setRange(optimal_spinner_id, 50, 150)
    ac.setStep(optimal_spinner_id, 1)
    ac.setValue(optimal_spinner_id, TYREINFO.optimal_temp)    
    ac.addOnValueChangeListener(optimal_spinner_id, onValueChanged)
  
  ac.log("Danny Giusa Tyre Temperatures loaded")
  return "Danny Giusa Tyre Temperatures"

def acShutdown():
  global TYREINFO
  if not os.path.exists(inidir):
    os.makedirs(inidir)
  if TYREINFO.needwriteini == 1:
    f = open(TYREINFO.carinifilepath, "w")
    f.write("optimal={0}".format(TYREINFO.optimal_temp))
    f.close()

def onValueChanged(value):
  global TYREINFO
  TYREINFO.optimal_temp = value
  TYREINFO.needwriteini = 1

def onFormRender(deltaT):
  global TYREINFO 
  tFL, tFR, tRL, tRR = ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)
  pFL, pFR, pRL, pRR = ac.getCarState(0, acsys.CS.DynamicPressure)
  dFL, dFR, dRL, dRR = ac.getCarState(0, acsys.CS.TyreDirtyLevel)
  wFL, wFR, wRL, wRR = readTyreWear()  
  TYREINFO.setTemp(tFL, tFR, tRL, tRR)
  TYREINFO.setPressure(pFL, pFR, pRL, pRR)
  #TYREINFO.setDirt(dFL, dFR, dRL, dRR)
  TYREINFO.setWear(wFL, wFR, wRL, wRR)
  TYREINFO.setMaxT(tFL, tFR, tRL, tRR)
  TYREINFO.setMaxP(pFL, pFR, pRL, pRR)
  drawTyresAll(w_tyre, h_tyre, round(tFL, 4), round(tFR, 4), round(tRL, 4), round(tRR, 4), dFL, dFR, dRL, dFR)

def readTyreWear():
  shmHandle = mmap.mmap(0, 256, "acpmf_physics")
  shmHandle.seek(30*4)
  data = shmHandle.read(4*4)
  shmHandle.close()  
  return struct.unpack("<ffff", data)

def drawTyresAll(w, h, tFL, tFR, tRL, tRR, dFL, dFR, dRL, dRR):
  drawTyres(x_tyre_position, y_tyre_position, w, h, tFL)
  drawTyres(x_tyre_position + x_space - x_tyre_space, y_tyre_position, w, h, tFR)
  drawTyres(x_tyre_position, y_tyre_position + y_space, w, h, tRL)
  drawTyres(x_tyre_position + x_space - x_tyre_space, y_tyre_position + y_space, w, h, tRR)
  drawTyresDirt(x_tyre_position + x_tyredirt_space, y_tyre_position + h_tyre, w_tyredirt, 0, dFL)
  drawTyresDirt(x_tyre_position + x_space - x_tyre_space + x_tyredirt_space, y_tyre_position + h_tyre, w_tyredirt, 0, dFR)
  drawTyresDirt(x_tyre_position + x_tyredirt_space, y_tyre_position + y_space + h_tyre, w_tyredirt, 0, dRL)
  drawTyresDirt(x_tyre_position + x_space - x_tyre_space + x_tyredirt_space, y_tyre_position + y_space + h_tyre, w_tyredirt, 0, dRR)

def drawTyres(x, y, w, h, temp):
  colorTyres(temp)
  ac.glQuad(x, y, w, h)
 
def drawTyresDirt(x, y, w, h, dirt):
  ac.glColor4f(0.9, 0.6, 0.2, 1)
  ac.glQuad(x, y, w, -(10 * dirt))
   
def colorTyres(temp):
  global TYREINFO
  hue = (TYREINFO.optimal_temp + 0.5 * temp_range - temp) / temp_range * 240
  if hue < 0: hue = 0
  elif hue > 240: hue = 240 
  r, g, b = hsv2rgb(hue, 1, 0.8)
  ac.glColor4f(r, g, b, 1)

def hsv2rgb(h, s, v):
  h = float(h)
  s = float(s)
  v = float(v)
  h60 = h / 60.0
  h60f = math.floor(h60)
  hi = int(h60f) % 6
  f = h60 - h60f
  p = v * (1 - s)
  q = v * (1 - f * s)
  t = v * (1 - (1 - f) * s)
  r, g, b = 0, 0, 0
  if hi == 0: r, g, b = v, t, p
  elif hi == 1: r, g, b = q, v, p
  elif hi == 2: r, g, b = p, v, t
  elif hi == 3: r, g, b = p, q, v
  elif hi == 4: r, g, b = t, p, v
  elif hi == 5: r, g, b = v, p, q  
  return r, g, b
  
def getValidFileName(filename):
  return "".join(c for c in filename if c in validFilenameChars)
