#!/usr/bin/env python2.7


#############Main parameters

wd='/data/home/mroczek/alpevent/'
eventcsv='/data/home/mroczek/alpevent/Q1-31.csv'
stationcsv='/data/home/mroczek/alpevent/stations.csv'
minmag=6
minepi=30
maxepi=95
ws=-10
we=50
sortby="event"
fhi=2
flo=0.03
model="iasp91"
mode="continue" 



###########
execfile(wd+"dowload_events_functions.py")
###Read events csv
with open(eventcsv, 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    rs=[x for x in reader]
nrs=np.asarray(rs)
try:
    tind=np.arange(len(rs[0]))[nrs[0] == "time"][0]
    latind=np.arange(len(rs[0]))[nrs[0] == "latitude"][0]
    lonind=np.arange(len(rs[0]))[nrs[0] == "longitude"][0]
    dind=np.arange(len(rs[0]))[nrs[0] == "depth"][0]
    magind=np.arange(len(rs[0]))[nrs[0] == "mag"][0]
    idind=np.arange(len(rs[0]))[nrs[0] == "id"][0]
except IndexError:
    raise ValueError("Required event column missing or mislabelled")

evtimes=np.asarray([UTCDateTime(x[tind]) for x in nrs[1:]])
lats=np.asarray([float(x[latind]) for x in nrs[1:]])
lons=np.asarray([float(x[lonind]) for x in nrs[1:]])
dps=np.asarray([float(x[dind]) for x in nrs[1:]])
mags=np.asarray([float(x[magind]) for x in nrs[1:]])
ids=np.asarray([x[idind] for x in nrs[1:]])

evmat=np.column_stack((ids,evtimes,lats,lons,dps,mags))

evmat=evmat[evmat[:,5] >= minmag]

##

###Read stations csv

with open(stationcsv, 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    ss=[x for x in reader]

nss=np.asarray(ss)
netalp=False
statind=np.arange(len(nss[0]))[nss[0] == "station"][0]
try:
    netind=np.arange(len(nss[0]))[nss[0] == "network"][0]
except IndexError:
    netalp=True
    print("No network column found; defaulting to _ALPARRAY")

stations=[x[statind] for x in nss[1:]]
if netalp:
    networks=np.repeat('_ALPARRAY',len(stations))
else:
    networks=[x[netind] for x in nss[1:]]

##

##Read station metadata

client = RoutingClient("eida-routing")
inv=client.get_stations(network=networks[0], station=stations[0],starttime=min(evtimes),endtime=max(evtimes),includerestricted=True,level="channel")
for i in np.arange(len(stations)):
    try:
        inv+=client.get_stations(network=networks[i], station=stations[i],starttime=min(evtimes),endtime=max(evtimes),includerestricted=True,level="channel")
    except:
        print("No station information")

missing_stat=[]
for st in np.arange(len(stations)):
    tinv=inv.select(station=stations[st])
    if len(tinv) == 0:
        missing_stat.append(["*",stations[st],networks[st],"missing_stat"])

##
execfile(wd+"dowload_events_functions.py")

comp,fail=dl_BH_HH(evmat,wd=wd,stations=stations,inv=inv,component="BH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi,mode="all")







os.remove(wd+"req.txt")