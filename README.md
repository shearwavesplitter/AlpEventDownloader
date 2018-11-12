# AlpEventDownloader

## Requires python version 2.7

## About

This script/functions act as a wrapper for the new fdsnws_fetch which is replacing arclink_fetch. Its main purpose is to list the stations and events for which data is missing or incomplete.  

Not all datacentres have implemented fdsnws_fetch however this should be very close (only weeks if not already).

### Advantages
* Allows restricted data to be downloaded
* Creates lists of events/stations where the download has failed or the data is incomplete/missing
* Downloaded events are written straight to .sac files and contain all important event and station information
* If the script is interrupted it can continue where it left off
* Failed events can be re-attempted

## [Bug reports and suggestions](https://github.com/shearwavesplitter/AlpEventDownloader/issues)

## Installation

### For fdsn_fetch backend
Open your preferred python enviroment (requires python 2.7)
```python
pip install fdsnwsscripts
```

### For arclink_fetch backend 
Open your preferred python enviroment
[Download the standalone client from here](https://www.seiscomp3.org/download.html)
e.g. installation for Ubuntu
```bash
sudo dpkg -i ~/arclinkfetch_2015.300_all.deb 
sudo apt-get install -f
```

### Other requirements
* obspy v1.1

Misc. packages (should be included with standard obspy installation)
* numpy
* csv
* subprocess
* os
* time

## Restricted data (Z3 etc.)
### fdsn_fetch (not fully implemented)
1. Get an invite from the Alparray group
2. Visit [here](https://geofon.gfz-potsdam.de/eas/) and request a token 
3. You will be asked to log in. If you haven't registered yet select "Register a new account"
4. Select "Create B2ACCESS account (username only)"
5. Fill in your details selecting "EPOS" under "Apply for membership"
6. Request to be added to AlpArray by an administrator
7. Return to [here](https://geofon.gfz-potsdam.de/eas/), log in, and request the token
8. Save the token in ~/.eidatoken 
9. fdsnws_fetch will automatically read the token

### arclink_fetch
1. Set the arclink_fetch parameter to your keyword (uniquely provided to each AASN Core Member)

## How to run

1. Create the event and station .csv files with the proper columns
2. Create a working directory
3. Update the "main parameters" and paths in download_events_script.py 
4. Run the script download_events_script.py 

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

**all**
 * Redownload everything

**continue**
 * Do not re-attempt any already attempted files 
 * Recommended (works when running for the first time as well)

**retry**
 * Re-attempt to download failed events

## .csv format

* Event .csv requires columns with the titles (not including the description in brackets):
  1. time (obspy readable format)
  2. latitude
  3. longitude
  4. depth (km)
  5. mag (magnitude)
  6. id (unique event identifier) - Not required unless you want to define your own event names
* Station .csv requires columns with the titles (not including the description in brackets):
  1. station (station name) - This can be a "*" to download from all stations
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

### retry mode

1. Stations from "missing_stations" are reattempted for all events
2. Events/stations from "missing_events" are attempted for BH (except those outside of the epicentral distance band)
3. Events/stations that fail for BH are attempted for HH (if HH also failed previously)
4. Newly completed events are added to "completed_events" and removed from "missing_events"

## What these scripts **don't** (currently) do
* Beyond missing data, there is no quality control (see pitfalls). 


## Potential pitfalls
* ZNE misorentations are **not** corrected for (even if rotated to RT or LQT). Component azimuth and dip information is lost from the sac headers if RT/LQT rotation is performed. This is because many stations have wrong component azimuth/dip information. 
* "missing_val" functionality hasn't been thoroughly tested
* An event can be flagged for missing_val but still have data downloaded (e.g. only two of the components)
* Events are cut so that they are the same length (npts could vary between events).
* Cut events will be flagged under missing_vals if they number of missing samples exceeds 10%
* Running multiple instances should be OK (just set mode to continue and summary files will contain events from both instances)
* If downsample==True and the actual sampling rate isn't a integer multiple of 20 then resample will be used instead of decimate
* Stations with sampling rates below 20 Hz won't be resampled at 20 Hz
