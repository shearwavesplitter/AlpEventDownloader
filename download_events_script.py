#!/usr/bin/env python2.7
#Requires fdsnwsscripts (pip install fdsnwsscripts)
#Create a working directory
#Update paths
#Run script
#View readme for further instructions

#############Main parameters

#Working directory where data will be saved (requires the trailing "/")
wd='/data/home/mroczek/alpevent/'

#Directory containing the functions document
fd="/data/home/mroczek/AlpEventDownloader/dowload_events_functions.py"

#Path to the events csv file
eventcsv='/data/home/mroczek/AlpEventDownloader/example_events.csv'

#Path to the events csv file. Note: A "*" entry means download all stations available for that network (_ALPARRAY if no network name is provided)
stationcsv='/data/home/mroczek/AlpEventDownloader/example_stations.csv'

#minimum magnitude (events below this value will be completely ignored)
minmag=5 

#minimum epicentral distance
minepi=30

#maximum epicentral distance
maxepi=95

#Window start time (seconds relative to predicted P-wave arrival time)
ws=-10  

#Window end time (seconds relative to predicted P-wave arrival time)
we=50 

#Sort by events by either "station" or "event"
sortby="event" 

#High value (Hz) for 2-pole butterworth bandpass filter (zerophase)
fhi=2 

# Low value (Hz) for 2-pole butterworth bandpass filter (zerophase)
flo=0.03 

#Earth model for predicting P-wave travel time (see obspy for options)
model="iasp91" 

#Mode for running; options include "all" to download everything, "continue" to continue, or "retry" to retry failed events
mode="continue"



###########
##Source functions
execfile(fd)
###Read events csv
##
evmat,evtimes=read_eventcsv(eventcsv,minmag=minmag)

###Read stations csv
stations,networks=read_stationcsv(stationcsv)
##

###Populate * wild card
stations,networks=populate(stations,networks,evtimes)
##

###Read station metadata
inventory,missing_stat,stations,networks=stat_meta(wd,stations,networks,evtimes=evtimes,mode=mode)
##

###Begin download
comp,fail=dl_BH_HH(evmat,wd=wd,stations=stations,networks=networks,inv=inventory,minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi,mode=mode,mod=model)
##

