#!/usr/bin/env python2.7
import sys
from obspy import UTCDateTime
#requires python version2.7
#Requires fdsnwsscripts for fdsn=True (pip install fdsnwsscripts)
#Requires standalone arclink_fetch client for fdsn=False
#Create a working directory
#Update paths
#Run script
#View readme for further instructions

#############Main parameters
#Working directory where data will be saved (requires the trailing "/")
wd='/data/home/mroczek/Dropbox/alpevent/'

#Directory containing the functions document
fd="/data/home/mroczek/AlpEventDownloader/download_events_functions.py"

###########EVENTS###################
#Path to the events csv file
eventcsv='/data/home/mroczek/AlpEventDownloader/example_events.csv'
##OR using an available catalog
useclient=True
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
stationcsv='/data/home/mroczek/AlpEventDownloader/example_stations.csv'
network="_ALPARRAY"
#Set c_inv equal to an obspy inventory (e.g. from read_inventory or get_stations) if you want to use your own station inventory rather than download a new one
c_inv=[]
#Or get stations from client in lat/longbox (leave True if using c_inv)
usestatclient=True
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
if sys.version_info[0] >= 3:
    #exec(open(fd).read())
    raise Exception("Requires python 2.7")
else:
    execfile(fd)
