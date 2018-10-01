# AlpEventDownloader

## Requires python version 2.7

## About

This script/functions act as a wrapper for the new fdsnws_fetch which is replacing arclink_fetch. Its main purpose is to list the stations and events for which data is missing or incomplete.  

### Advantages
* Allows restricted data to be downloaded
* Creates lists of events/stations where the download has failed or the data is incomplete/missing
* Downloaded events are written straight to .sac files and contain all important event and station information
* If the script is interrupted it can continue where it left off
* Failed events can be re-attempted

## [Bug Reports](https://github.com/shearwavesplitter/AlpEventDownloader/issues)

## Installation

```python
pip install fdsnwsscripts
```

## Restricted data (Z3 etc.)
1. Get an invite from the Alparray group
2. Register in B2ACCESS
3. Request a token [here](https://geofon.gfz-potsdam.de/eas/)
4. Save the token in ~/.eidatoken (create the hidden folder if needed)
5. fdsnws_fetch will automatically read the token

## How to run

1. Create the event and station .csv files with the proper columns
2. Create a working directory
3. Update the "main parameters" in download_events_script.py
4. Run the script

## Output
* .sac files for each event sorted either by event name or by station
* "missing_stations" .csv file which contains stations that are not available for any event
* "missing_events" .csv file which contains the columns 
 1. Event ID
 2. Station
 3. Network
 4. Channel (BH or HH)
 5. Comment
  * "no_data" if there is no data available
  * "missing_val" if some of the trace is missing
  * "epi_dist" if the epicentral distance is outside the allowed band
* "completed_events" .csv contains the station, network, and component for events that have been succesfully downloaded

## Optional modes:

**continue**
 * Do not re-attempt any already attempted files 

**all**
 * Redownload everything

**retry**
 * Only re-attempted failed downloads (not yet implemented) 

## .csv format

* Event .csv requires columns with the titles (not including the description in brackets):
  1. time (obspy readable format)
  2. latitude
  3. longitude
  4. depth (km)
  5. mag (magnitude)
  6. id (unique event identifier)
* Station .csv requires columns with the titles (not including the description in brackets):
  1. station (station name)
  2. network (if not included defaults to _ALPARRAY)

## File contents
**dowload_events_functions.py**
 * The workhorse functions used for download

**download_events_script.py**
 * The script for downloading events

**example_events.csv**
 * Example of the events .csv file

**example_stations.csv**
 * Example of the stations .csv file

## Details

1. Requests all BH* data from all stations for a single event
2. Individually Re-requests BH* data for all stations with missing or incomplete BH* data
3. Requests all HH* data for stations with missing or incomplete BH* data
4. Individually requests HH* data for stations with missing or incomplete HH* data
5. Applies broad bandpass filter and then detrends
6. Writes out sac files for each event including header information

## Potential pitfalls
* There currently may be problems if there are different stations with the same name
* Running multiple instances should be OK (just set mode to continue and summary files will contain events from both instances)

## To do
* Include instructions for downloading restricted data