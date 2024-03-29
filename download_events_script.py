#!/usr/bin/env python
import sys
from obspy import UTCDateTime
#requires python version2.7
#Requires fdsnwsscripts for fdsn=True (pip install fdsnwsscripts)
#arclink_fetch client no longer works
#Create a working directory
#Update paths and options (default is to download example events from example stations)
#Run script
#View readme for further instructions

#############Main parameters
#Working directory where data will be saved (requires the trailing "/")
wd='/home/stefan/alpevent/'

#Directory containing the functions document
fd="/home/stefan/AlpEventDownloader/download_events_functions.py"

###########EVENTS###################
#Path to the events csv file
eventcsv='/home/stefan/AlpEventDownloader/example_events.csv'
##OR using an available catalog
useclient=False
cl="USGS"
starttime=UTCDateTime("2009-01-01")
endtime=UTCDateTime("2018-12-01")
###Create unique event names YYYY.DDD.HH.MM.SS.NW.STA.C.SAC
cnames=True
####################################


###########STATIONS###################
#Client (routing clients are "iris-federator" and "eida-routing")
client_name="eida-routing"
#Is this a routing client?
rclient=True
#Path to the stations csv file. Note: A "*" entry means download all stations available for that network (_ALPARRAY if no network name is provided)
stationcsv='/home/stefan/AlpEventDownloader/example_stations.csv'
network="_ALPARRAY"
#Set c_inv equal to an obspy inventory (e.g. from read_inventory or get_stations) if you want to use your own station inventory rather than download a new one
c_inv=[]
#Or get stations from client in lat/longbox (leave True if using c_inv)
usestatclient=False
network="_ALPARRAY"
minlatitude=-90
minlongitude=-180
maxlatitude=90
maxlongitude=180
includeZS=False #Include the ZS network (defaults as part of _ALPARRAY)
#ZNE rotations (correct station azimuths with .csv file?)
znepath='/data/home/mroczek/AlpEventDownloader/rotations.csv'
rotzne=False
####################################


#Phase (see obspy for detailed options)
phase="P"

#minimum magnitude (events below this value will be completely ignored)
minmag=5.5

#minimum epicentral distance
minepi=30

#maximum epicentral distance
maxepi=95

#Window start time (seconds relative to predicted P-wave arrival time)
ws=-120  

#Window end time (seconds relative to predicted P-wave arrival time)
we=120

#Sort by events by either "station" or "event"
sortby="event" 

#High value (Hz) for 2-pole butterworth bandpass filter (zerophase) (No filter if set to None)
fhi=None #

# Low value (Hz) for 2-pole butterworth bandpass filter (zerophase) (no filter if set to None)
flo=0.03 

#Downsample to 20Hz? (using decimate unless the actual sampling rate isn't an integer multiple of 20)
downsample=True

#Rotate coordinates? "NE->RT" or "ZNE->LQT" or None (Warning: does not correct ZNE misorientations listed in metadata)
rotrt= None

#Earth model for predicting P-wave travel time (see obspy for options)
model="iasp91" 

#Mode for running; options include "all" to download everything, "continue" to continue, or "retry" to retry failed events
mode="continue"


###########
##Source functions and start download
exec(open(fd).read())
