# AlpEventDownloader 1.2

## Requires python version 2.7

## About

This script/functions act as a wrapper for the new fdsnws_fetch. Its main purpose is to list the stations and events for which data is missing or incomplete.  

Arclink_fetch is now depreciated but can still can be still enabled in download_events_functions.py.

### Advantages
* Allows restricted data to be downloaded
* Creates lists of events/stations where the download has failed or the data is incomplete/missing
* Downloaded events are written straight to .sac files and contain all important event and station information
* If the script is interrupted it can continue where it left off
* Failed events can be re-attempted

## [Bug reports and suggestions](https://github.com/shearwavesplitter/AlpEventDownloader/issues)

## Installation

Open your preferred python environment
```python
pip install fdsnwsscripts
```

### Other requirements
* python2.7
* obspy v1.1

Misc. packages (should be included with standard obspy installation)
* numpy1.15
* csv
* subprocess
* os
* time

Other:
* m2crypto (not required for Z3 but required for ZS)

## Restricted data (Z3 etc.)
### fdsnws_fetch
1. Visit [here](https://geofon.gfz-potsdam.de/eas/) and request a token 
2. You will be asked to log in. If you haven't registered yet select "Register a new account"
3. Select "Create B2ACCESS account (username only)"
4. Fill in your details selecting "EPOS" under "Apply for membership"
5. Verify that you are on the [list of approved users](http://www.alparray.ethz.ch/en/seismic_network/backbone/management/)
6. Request to be added to AlpArray by an administrator ([heimers AT sed.ethz.ch](mailto:heimers@sed.ethz.ch) or [jclinton AT sed.ethz.ch](mailto:jclinton@sed.ethz.ch)). 
7. Return to [here](https://geofon.gfz-potsdam.de/eas/), log in, and request the token
8. Save the token as ~/.eidatoken 
9. fdsnws_fetch will automatically read the token

## How to run

1. Create a working directory
2. Update the "main parameters" and paths in download_events_script.py 
3. (Optional) Create the event and station .csv files with the proper columns
4. Run the script download_events_script.py 

## Output
* .sac files for each event sorted either by event name or by station
* Event back azimuth (baz), incidence angle (user0), and slowness (s/deg - user1) are written into the sac headers
* "missing_stations" .csv file which contains stations that are not available for any event
* "missing_events" .csv file which contains the columns 
  1. Event ID
  2. Station
  3. Network
  4. Channel (BH or HH)
  5. Comment
    * "no_data" if there is no data available
    * "missing_val" if some of the trace is missing (this funcionality doesn't appear to be active)
    * "epi_dist" if the epicentral distance is outside the allowed band
* "completed_events" .csv contains the station, network, and component for events that have been successfully downloaded

## ZNE Rotations
The part of the code that corrects ZNE rotations hasn't been thoroughly tested yet. However, there are some SAC headers to help identify traces that have failed:
* Rotations use the median value from the .csv file if the number of samples is greater than 4
* user3 is set to 1 if a ZNE rotation has been attempted (i.e. the table contains azimuth data for that station) otherwise 0
* user2 is set to 1 if the rotation was successful (otherwise 0). 
Most failures to rotate will occur due to nan values in the trace (i.e. traces of different lengths) causing an unrotated trace to be written to file (with the header user2=0).
The correct azimuths in the .csv file are provided by Gesa Petersen and are calculated from Rayleigh wave polarisations.

## Optional modes:

**all**
 * Redownload everything

**continue**
 * Do not re-attempt any already attempted files 
 * Recommended (works when running for the first time as well)

**retry**
 * Re-attempt to download failed events

## .csv format (Optional)

* Event .csv requires columns with the titles (not including the description in brackets):
  1. time (obspy readable format)
  2. latitude
  3. longitude
  4. depth (km)
  5. mag (magnitude)
  6. (optional) id (unique event identifier) - Not required unless you want to define your own event names
* Station .csv requires columns with the titles (not including the description in brackets):
  1. station (station name) - This can be a "*" to download from all stations
  2. network (if not included defaults to _ALPARRAY) **It is recommended not to use _ALPARRAY as some stations are missing**

## File contents
**download_events_functions.py**
 * The workhorse functions used for download

**download_events_script.py**
 * The script for downloading events

**example_events.csv (optional)**
 * Example of the events .csv file

**example_stations.csv (optional)**
 * Example of the stations .csv file

## Details
1. Requests all BH* data from all stations for a single event
2. Individually Re-requests BH* data for all stations with missing or incomplete BH* data
3. Requests all HH* data for stations with missing or incomplete BH* data
4. Individually requests HH* data for stations with missing or incomplete HH* data
5. Applies broad bandpass filter and then detrends
6. Writes out sac files for each event including header information (Event name (KEVNM) skips the leading 20 (or 19) due to having a 16 character limit)

### retry mode

1. Stations from "missing_stations" are reattempted for all events
2. Events/stations from "missing_events" are attempted for BH (except those outside of the epicentral distance band)
3. Events/stations that fail for BH are attempted for HH (if HH also failed previously)
4. Newly completed events are added to "completed_events" and removed from "missing_events"

## What these scripts **don't** (currently) do
* Beyond missing data, there is no quality control (see pitfalls). 


## Potential pitfalls
* If ZNE orientation correction is attempted some events may fail so check the sac header user3 to make sure it is set to 1
* If the RT or LQT rotation fails then the components will be left as ZNE
* "missing_val" functionality hasn't been thoroughly tested
* An event can be flagged for missing_val but still have data downloaded (e.g. only two of the components)
* Events are cut so that they are the same length (npts could vary between events).
* Cut events will be flagged under missing_vals if they number of missing samples exceeds 10%
* Running multiple instances should be OK (just set mode to continue and summary files will contain events from both instances)
* If downsample==True and the actual sampling rate isn't an integer multiple of 20 then resample will be used instead of decimate
* The downsample anti-aliasing filter is now zerophase (obspy default is not)
* Stations with sampling rates below 20 Hz won't be resampled at 20 Hz
* Event name (KEVNM) for sac files skips the leading 20 (or 19) due to having a 16 character limit
