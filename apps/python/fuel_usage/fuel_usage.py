################################################################################
# Fuel Usage App for Assetto Corsa by Thomas Gocke
# https://github.com/flitzi/AC_APPS
# 
# Shows from left to right  -the fuel left in tank  -average fuel per lap  -laps left until tank is empty 
# The out lap is skipped, so you need to drive 2 laps before calculation starts.
# The average fuel usage per lap is stored in C:/Users/[YourUserName]/[CarName]_[TrackName].ini
# The stored value (if existing) is used for the first two laps until the new calculation is started
#
# Changelog:
#
# 1.0 
# - first release
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
inidir = expanduser("~") + "/AC_fuel_usage/"

###valid file name characters
validFilenameChars = "-_() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

###appsize
x_app_size = 300
y_app_size = 50
###startingpoint of first label
x_start = 17
y_start = 27

################## CHANGE BACKROUND HERE ################## 
background = 0
################## CHANGE BACKROUND HERE ##################

class Fuel_Usage:  

  def __init__(self, app, x, y):    
    
    self.laps = 0
    self.averageFuelPerLap = 0
    self.fuelAtLapStart = 0
    
    self.inifilepath = inidir + getValidFileName(ac.getCarName(0)) +"_" + getValidFileName(ac.getTrackName(0)) + ".ini"
    
    if os.path.exists(self.inifilepath):
      f = open(self.inifilepath, "r")
      self.averageFuelPerLap = float(f.readline()[6:])
      f.close()
    
    ##initialize labels
    
    self.remainingLabel = ac.addLabel(app, "remainingLabel")
    self.averageFuelPerLapLabel = ac.addLabel(app, "averageFuelPerLapLabel")
    self.lapsLeftLabel = ac.addLabel(app, "lapsLeftLabel")   
    
    ##set label positions
    
    ac.setPosition(self.remainingLabel, x, y)
    ac.setPosition(self.averageFuelPerLapLabel, x + 100, y)
    ac.setPosition(self.lapsLeftLabel, x + 200, y)    
    
    ##set label alignments
    
    ac.setFontAlignment(self.remainingLabel, "left")
    ac.setFontAlignment(self.averageFuelPerLapLabel, "left")
    ac.setFontAlignment(self.lapsLeftLabel, "left")    
    
    ##set font size
    
    ac.setFontSize(self.remainingLabel, 16)
    ac.setFontSize(self.averageFuelPerLapLabel, 16)
    ac.setFontSize(self.lapsLeftLabel, 16)
    
    ac.setText(self.averageFuelPerLapLabel, "--- l/lap")
    ac.setText(self.lapsLeftLabel, "--- laps")
  
  def setFuel(self, remaining, laps):
    ac.setText(self.remainingLabel, "{0} l".format(round(remaining, 1)))
    if laps != self.laps:
      if laps >= 2 and self.fuelAtLapStart > remaining:
        self.averageFuelPerLap = (self.averageFuelPerLap * (laps - 2) + self.fuelAtLapStart - remaining) / (laps - 1)
      self.fuelAtLapStart = remaining
      self.laps = laps
    if self.averageFuelPerLap > 0:
      ac.setText(self.averageFuelPerLapLabel, "{0} l/lap".format(round(self.averageFuelPerLap, 2)))
      ac.setText(self.lapsLeftLabel, "{0} laps".format(round(remaining / self.averageFuelPerLap, 1)))

def acMain(ac_version):
  global fuelUsage
  appWindow = ac.newApp("Fuel Usage")
  ac.drawBackground(appWindow, background)  
  ac.drawBorder(appWindow, background)
  ac.setBackgroundOpacity(appWindow, background)
  ac.setSize(appWindow, x_app_size, y_app_size)
  fuelUsage = Fuel_Usage(appWindow, x_start, y_start)  
  ac.addRenderCallback(appWindow, onFormRender)
  
  ac.log("Fuel Usage App loaded")
  return "Fuel Usage App"

def acShutdown():
  global fuelUsage
  if not os.path.exists(inidir):
    os.makedirs(inidir)
  if fuelUsage.averageFuelPerLap > 0:
    f = open(fuelUsage.inifilepath, "w")
    f.write("l/lap={0}".format(fuelUsage.averageFuelPerLap))
    f.close()

def onFormRender(deltaT):
  global fuelUsage   
  remaining = readFuel()  
  laps = ac.getCarState(0, acsys.CS.LapCount)
  fuelUsage.setFuel(remaining, laps)  

def readFuel():
  shmHandle = mmap.mmap(0, 256, "acpmf_physics")
  shmHandle.seek(3*4)
  data = shmHandle.read(1*4)
  shmHandle.close()  
  return struct.unpack("<f", data)[0]

def getValidFileName(filename):
  return "".join(c for c in filename if c in validFilenameChars)
