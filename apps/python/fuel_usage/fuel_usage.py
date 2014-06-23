################################################################################
# Fuel Usage App for Assetto Corsa by Thomas Gocke
# https://github.com/flitzi/AC_APPS
# 
# Shows from left to right  -the fuel left in tank  -average fuel per lap  -laps left until tank is empty 
# The out lap is skipped, so you need to drive 2 laps before calculation starts.
# The average fuel usage per lap is stored in C:/Users/[YourUserName]/AC_fuel_usage/[CarName]_[TrackName].ini
# The stored value (if existing) is used for the first two laps until the new calculation is started
#
# Changelog:
#
# 1.0 
# - first release
#
# 1.1
# - added average fuel consumption in liters per 100 km and inst. fuel consumption (also in liters per 100 km)
# - fixed bug in average per lap calculation when removing fuel in pits (leaving pits with less fuel than at pit entry)
#
# 1.2
# - fixed bug for game modes not starting in pit (hotlap, time attack)
#
# 1.3
# - added miles per gallon calculation (change constant milesPerGallon to True)
# - fixed liters per 100km calculation after restart and not starting in pit (distance travelled not resetted in AC?)
#
# 1.5
# - when crossing the line, fuel consumption of last lap and remaining laps based on this value are shown for a couple of seconds (blinking)
#
# 1.6
# - updated to AC 0.20 shared memory struct
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
y_app_size = 66
###startingpoint of first label
x_start = 7
y_start = 26

################## CHANGE FOR MILES PER GALLON HERE #######
milesPerGallon = False
################## CHANGE FOR MILES PER GALLON HERE #######

################## CHANGE BACKROUND HERE ##################
background = 0
################## CHANGE BACKROUND HERE ##################

class Fuel_Usage:  

  def __init__(self, app, x, y):
    
    self.AverageFuelPerLap = 0.0
    self.FuelLastLap = 0.0
    self.completedLaps = 0.0
    self.fuelAtLapStart = 0.0
    self.distanceTraveledAtStart = 0.0
    self.fuelAtStart = 0.0
    self.lastFuelMeasurement = 0.0
    self.lastDistanceTraveled = 0.0
    self.counter = 0
    self.updatecounter = 0
    
    self.inifilepath = inidir + self.getValidFileName(ac.getCarName(0)) +"_" + self.getValidFileName(ac.getTrackName(0)) + ".ini"
    
    ##initialize labels
    
    self.remainingLabel = ac.addLabel(app, "remainingLabel")
    self.averageFuelPerLapLabel = ac.addLabel(app, "averageFuelPerLapLabel")
    self.lapsLeftLabel = ac.addLabel(app, "lapsLeftLabel")
    self.averageFuelPer100kmLabel = ac.addLabel(app, "averageFuelPer100km")
    self.instFuelLabel = ac.addLabel(app, "instFuel")
    
    ##set label positions
    
    ac.setPosition(self.remainingLabel, x, y)
    ac.setPosition(self.averageFuelPerLapLabel, x + 93, y)
    ac.setPosition(self.lapsLeftLabel, 100 - x, y)
    ac.setPosition(self.averageFuelPer100kmLabel, x + 93, y + 19)
    ac.setPosition(self.instFuelLabel, 100 - x, y + 19)
    
    ##set label alignments
    
    ac.setFontAlignment(self.remainingLabel, "left")
    ac.setFontAlignment(self.averageFuelPerLapLabel, "left")
    ac.setFontAlignment(self.lapsLeftLabel, "right")
    ac.setFontAlignment(self.averageFuelPer100kmLabel, "left")
    ac.setFontAlignment(self.instFuelLabel, "right")
    
    ##set font size
    
    ac.setFontSize(self.remainingLabel, 32)
    ac.setFontSize(self.averageFuelPerLapLabel, 16)
    ac.setFontSize(self.lapsLeftLabel, 16)
    ac.setFontSize(self.averageFuelPer100kmLabel, 16)
    ac.setFontSize(self.instFuelLabel, 16)

    if os.path.exists(self.inifilepath):
      f = open(self.inifilepath, "r")
      self.AverageFuelPerLap = float(f.readline()[6:])
      f.close()
    
    ac.setText(self.remainingLabel, "--- l")
    ac.setText(self.averageFuelPerLapLabel, "--- l/lap")
    ac.setText(self.lapsLeftLabel, "--- laps")
    if milesPerGallon:
      ac.setText(self.averageFuelPer100kmLabel, "--- mpg")
    else:
      ac.setText(self.averageFuelPer100kmLabel, "--- l/100km")
    ac.setText(self.instFuelLabel, "--- inst.")
  
  def getValidFileName(self, filename):
    return "".join(c for c in filename if c in validFilenameChars)
  
  def lPer100kmToMPG(self, lp100km):
    if lp100km == 0:
      return 999.0
    else:
      return 235.214584 / lp100km
  
  def Update(self):
    remaining = self.readFuel() #read remaining fuel from shared memory
    completedLaps, distanceTraveled, isInPit = self.readInfo() #read completedLaps, distanceTraveled, isInPit from shared memory
    
    if isInPit == 1 or self.lastFuelMeasurement < remaining or self.lastFuelMeasurement - 2 > remaining: #if in pit or restarted (refilled fuel or taken fuel out)
      self.fuelAtLapStart = 0 #set fuelAtLapStart to 0 so the coming lap will not be counted
      self.fuelAtStart = remaining
      self.distanceTraveledAtStart = distanceTraveled
    
    if completedLaps != self.completedLaps: #when crossed finish line
      if completedLaps >= 2 and self.fuelAtLapStart > remaining: #if more than 2 laps driven
        self.FuelLastLap = self.fuelAtLapStart - remaining # calculate fuel used last lap
        self.AverageFuelPerLap = (self.AverageFuelPerLap * (completedLaps - 2) + self.FuelLastLap) / (completedLaps - 1) #calculate AverageFuelPerLap
      self.fuelAtLapStart = remaining #reset fuelAtLapStart
      self.completedLaps = completedLaps #set completedLaps
      self.counter = 999
      self.updatecounter = 0
    
    if self.counter > 30: #if enough ticks for update
      ac.setText(self.remainingLabel, "{0} l".format(round(remaining, 1))) #set remaining fuel text
      if self.AverageFuelPerLap > 0:
        if self.updatecounter > 20 or self.FuelLastLap == 0:
          ac.setText(self.averageFuelPerLapLabel, "{0} l/lap".format(round(self.AverageFuelPerLap, 2))) #set averageFuelPerLap text
          ac.setText(self.lapsLeftLabel, "{0} laps".format(round(remaining / self.AverageFuelPerLap, 1))) #set lapsLeft text
        else:
          if self.updatecounter % 2 == 1:
            ac.setText(self.averageFuelPerLapLabel, "{0} last".format(round(self.FuelLastLap, 2))) #set fuel last lap text
            ac.setText(self.lapsLeftLabel, "{0} laps".format(round(remaining / self.FuelLastLap, 1))) #set lapsLeft with last lap consumption text
          else:
            ac.setText(self.averageFuelPerLapLabel, " ") #make text blinking
            ac.setText(self.lapsLeftLabel, " ") #make text blinking
      
      distance = distanceTraveled - self.lastDistanceTraveled #distance since last calculation update
      if distance > 0.01:
        lp100km = (self.lastFuelMeasurement - remaining) / distance * 100000
        if milesPerGallon:
          ac.setText(self.instFuelLabel, "{0} inst".format(round(self.lPer100kmToMPG(lp100km), 1))) #set inst. fuel consumption text in mpg
        else:
          ac.setText(self.instFuelLabel, "{0} inst".format(round(lp100km, 1))) #set inst. fuel consumption text
      else:
        if milesPerGallon: 
          ac.setText(self.instFuelLabel, "0 inst") #set inst. fuel consumption text if not moving in mpg
        else:
          ac.setText(self.instFuelLabel, "999 inst") #set inst. fuel consumption text if not moving
      
      distance = distanceTraveled - self.distanceTraveledAtStart #distance since last last pit
      if distance > 0.01:
        lp100km = (self.fuelAtStart - remaining) / distance * 100000
        if milesPerGallon:
          ac.setText(self.averageFuelPer100kmLabel, "{0} mgp".format(round(self.lPer100kmToMPG(lp100km), 1))) #set average fuel consumption text in mpg
        else:
          ac.setText(self.averageFuelPer100kmLabel, "{0} l/100km".format(round(lp100km, 1))) #set average fuel consumption text
      else:
        if milesPerGallon: 
          ac.setText(self.averageFuelPer100kmLabel, "0 mpg") #set average fuel consumption text if not moving in mpg
        else:
          ac.setText(self.averageFuelPer100kmLabel, "999 l/100km") #set average fuel consumption text if not moving
      
      self.lastFuelMeasurement = remaining #reset lastFuelMeasurement
      self.lastDistanceTraveled = distanceTraveled #reset lastDistanceTraveled
      self.updatecounter = self.updatecounter + 1 #increment update counter
      self.counter = 0 #reset counter
    
    self.counter = self.counter + 1 #increment counter
  
  def readFuel(self):
    shmHandle = mmap.mmap(0, 256, "acpmf_physics")
    shmHandle.seek(12)
    data = shmHandle.read(4)
    shmHandle.close()  
    return struct.unpack("<f", data)[0]
  
  def readInfo(self):
    shmHandle = mmap.mmap(0, 169, "acpmf_graphics")
    shmHandle.seek(72)    
    completedLaps = struct.unpack("<L", shmHandle.read(4))[0]
    shmHandle.seek(96)    
    distanceTraveled = struct.unpack("<f", shmHandle.read(4))[0]
    isInPit = struct.unpack("<L", shmHandle.read(4))[0]
    shmHandle.close()  
    return completedLaps, distanceTraveled, isInPit

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
  if fuelUsage.AverageFuelPerLap > 0:
    f = open(fuelUsage.inifilepath, "w")
    f.write("l/lap={0}".format(fuelUsage.AverageFuelPerLap))
    f.close()

def onFormRender(deltaT):
  global fuelUsage
  fuelUsage.Update()
