#!/usr/bin/env python2.7
import csv
import numpy as np
from fdsnwsscripts import fdsnws_fetch
from subprocess import call
from obspy.core.utcdatetime import UTCDateTime
import os
from obspy.clients.fdsn import RoutingClient
from obspy.core import read
from obspy.geodetics import locations2degrees
from obspy.taup import TauPyModel
from obspy import read_inventory
from obspy.io.sac import SACTrace
import time

###Paste function for creating .csv
def pasteR(vector,sep=" "):
    s=str(vector[0])
    for i in np.arange(1,len(vector)):
        s+=sep
        s+=str(vector[i])
    return(s)

#####Read event csv
def read_eventcsv(path,minmag=5.5):
    with open(path, 'rb') as csvfile:
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
    return(evmat,evtimes)

#######Read station csv
def read_stationcsv(path,defaultnet="_ALPARRAY"):
    with open(path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        ss=[x for x in reader]

    nss=np.asarray(ss)
    netalp=False
    statind=np.arange(len(nss[0]))[nss[0] == "station"][0]
    try:
        netind=np.arange(len(nss[0]))[nss[0] == "network"][0]
    except IndexError:
        netalp=True
        print("No network column found; defaulting to "+defaultnet)

    stations=[x[statind] for x in nss[1:]]
    if netalp:
        networks=np.repeat(defaultnet,len(stations))
    else:
        networks=[x[netind] for x in nss[1:]]
    return(stations,networks)


####Read station metadata
def stat_meta(wd,stations,networks,evtimes,routername="eida-routing",mode="continue",write=True):
    if mode == "retry":
        return([],[],[],[])
    if mode == "all":
        print("New download...")
    if mode == "continue":
        skip=[]
        with open(wd+"missing_stations", 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            ss=[skip.append(x) for x in reader]
        netstat=[x[1]+x[2] for x in skip]
        netstatin=[stations[x]+networks[x] for x in np.arange(len(stations))]
        stations=[stations[x] for x in np.arange(len(stations)) if netstatin[x] not in netstat]
        networks=[networks[x] for x in np.arange(len(networks)) if netstatin[x] not in netstat]
    client = RoutingClient(routername)
    inv=client.get_stations(network=networks[0], station=stations[0],starttime=min(evtimes),endtime=max(evtimes),includerestricted=True,level="channel")
    for i in np.arange(1,len(stations)):
        try:
            inv+=client.get_stations(network=networks[i], station=stations[i],starttime=min(evtimes),endtime=max(evtimes),includerestricted=True,level="channel")
        except:
            print(stations[i])
            print("No station information")

    missing_stat=[]
    mstatlist=[]
    mnetlist=[]
    for st in np.arange(len(stations)):
        tinv=inv.select(station=stations[st])
        if len(tinv) == 0:
            missing_stat.append(["*",stations[st],networks[st],"missing_stat"])
            mstatlist.append(stations[st])
            mstatlist.append(networks[st])

    if mode == "continue":
        wm="a+"
    else:
        wm="w"
    if write:
        file = open(wd+"missing_stations",wm) 
        for l in missing_stat:
            file.write(pasteR(l,sep=",")+"\n")
        file.close()

    ostat=[x[0].code for x in inv]
    onet=[x.code for x in inv]
    return(inv,missing_stat,ostat,onet)





##Main download function

def dl_event(evline,wd,stations,networks,inv,component="BH",minepi=30,maxepi=95,ws=-10,we=50,sortby="event",mod="iasp91",flo=0.03,fhi=2):
    model = TauPyModel(model=mod)
    failure=[]
    failure3=[]
    run=[]
    ev=evline
    t=ev[1]
    lat=ev[2]
    lon=ev[3]
    d=ev[4]
    mag=ev[5]
    id=ev[0]
    for j in np.arange(len(stations)):
        episkip=False
        subinv=inv.select(station=stations[j],network=networks[j],time=t)
        if len(subinv) > 0:
            net=subinv[0].code
            stat=subinv[0][0].code
            slat=subinv[0][0].latitude
            slon=subinv[0][0].longitude
            epi=locations2degrees(lat,lon,slat,slon)
            if epi < minepi or epi > maxepi:
                failure.append([id,stations[j],networks[j],component,"epi_dist"])
                episkip=True

        subinv=inv.select(station=stations[j],network=networks[j],time=t,channel=component+"*")
        if len(subinv) == 0 or episkip:
            if len(subinv) == 0 and not episkip:
                failure.append([id,stations[j],networks[j],component,"no_data"])
        else:
            if not (epi < minepi or epi > maxepi):
                ptime=model.get_travel_times(source_depth_in_km=d,distance_in_degree=epi,phase_list=["P"])
                ptrav=ptime[0].time
                wstart=t+ptrav+ws
                wend=t+ptrav+we
                run.append([id,stat,net,wstart,wend,ptrav])
    reqname="data/"+id+str(len(stations))+str(float(UTCDateTime.now()))
    if len(run) > 0:
        file = open(wd+reqname,"w") 
        for st in run:
            sst=st[3].format_arclink()
            est=st[4].format_arclink()
            line=[sst,est,st[2],st[1],component+"*","*",".\n"]
            file.write(pasteR(line))
        file.close()
        failure2=[]
        rstats=[x[1] for x in run]
        rnets=[x[2] for x in run]
        cmd="fdsnws_fetch -f "+wd+reqname+" "+"-o"+" "+wd+reqname+".mseed"
        os.system(cmd)
        fsize=os.path.getsize(wd+reqname+".mseed")
        if fsize == 0:
            for rl in run:
                failure2.append([rl[0],rl[1],rl[2],component,"no_data"])
                failstats=[x[1] for x in failure2]
                failnets=[x[2] for x in failure2]
        else:
            ms=read(wd+reqname+".mseed")
            ustnet=np.unique([[x.stats.station,x.stats.network] for x in ms],axis=0)
            pustnet=np.unique([x.stats.station+x.stats.network for x in ms],axis=0)
            sts=ustnet[:,0]
            nets=ustnet[:,1]
            failstats=[rstats[x] for x in np.arange(len(rstats)) if (rstats[x]+rnets[x] not in pustnet)]
            failnets=[rnets[x] for x in np.arange(len(rstats)) if (rstats[x]+rnets[x] not in pustnet)]
            for i in np.arange(len(failstats)):
                failure2.append([id,failstats[i],failnets[i],component,"no_data"])
            for l in np.arange(len(sts)):
                subst=sts[l]
                subms=ms.select(station=subst,network=nets[l])
                subms.merge()
                runline2=[x for x in run if x[2] == nets[l] and x[1] == subst][0]
                stt=runline2[3]
                ett=runline2[4]
                a=ws*-1
                o=a-runline2[5]
                subms.trim(starttime=stt,endtime=ett)
                subms.filter(type='bandpass',freqmin=flo,freqmax=fhi,zerophase=True,corners=2)
                subms.detrend()
                ts=[True for x in subms if x.stats.npts < (ws-we)*x.stats.sampling_rate]
                nan=[True for x in subms if sum(np.isnan(x.data)) > 0]
                if sum(ts) > 0:
                    failure2.append([id,subst,nets[l],component,"missing_vals"])
                else:
                    if sum(nan) > 0:
                        failure2.append([id,subst,nets[l],component,"missing_vals"])
                if sortby == "event":
                    wp=wd+"data/"+id+"/"
                if sortby == "station":
                    wp=wd+"data/"+subst+"/"
                if not os.path.exists(wp):
                    os.makedirs(wp)
                if len(subms) < 3:
                    failure2.append([id,subst,nets[l],component,"missing_vals"])
                for tr in subms:
                    trinv=inv.select(channel=tr.stats.channel,station=tr.stats.station,network=tr.stats.network,time=t)
                    sactr = SACTrace.from_obspy_trace(tr)
                    sactr.cmpaz=trinv[0][0][0].azimuth
                    sactr.cmpinc=trinv[0][0][0].dip+90 ##convert to degrees from vertical
                    sactr.stla=trinv[0][0].latitude
                    sactr.stlo=trinv[0][0].longitude
                    sactr.evdp=d
                    sactr.evlo=lon
                    sactr.evla=lat
                    sactr.mag=mag
                    sactr.a=a
                    sactr.o=o
                    sactr.stel=trinv[0][0].elevation
                    sactr.kevnm=runline2[0]
                    sactr.write(wp+id+"."+tr.stats.network+"."+tr.stats.station+"."+tr.stats.channel+".sac")
                failure.append([id,subst,nets[l],component,"completed"])
        os.remove(wd+reqname+".mseed")
        os.remove(wd+reqname)

        for i in np.arange(len(failure2)):
            stat=failure2[i][1]
            net=failure2[i][2]
            rline=[x for x in np.arange(len(rstats)) if stat == rstats[x] and net == rnets[x]]
            rline2=run[rline[0]]
            reqname="data/"+id+stat+net+str(float(UTCDateTime.now()))
            file = open(wd+reqname,"w") 
            sst=rline2[3].format_arclink()
            est=rline2[4].format_arclink()
            line=[sst,est,rline2[2],rline2[1],component+"*","*",".\n"]
            file.write(pasteR(line))
            file.close()
            cmd="fdsnws_fetch -f "+wd+reqname+" "+"-o"+" "+wd+reqname+".mseed"
            os.system(cmd)
            fsize=os.path.getsize(wd+reqname+".mseed")
            if fsize == 0:
                failure3.append([id,stat,net,component,"no_data"])
            else:
                subms=read(wd+reqname+".mseed")
                subms.merge()
                runline2=[x for x in run if x[2] == net and x[1] == stat][0]
                stt=runline2[3]
                ett=runline2[4]
                a=ws*-1
                o=a-runline2[5]
                subms.trim(starttime=stt,endtime=ett)
                subms.filter(type='bandpass',freqmin=flo,freqmax=fhi,zerophase=True,corners=2)
                subms.detrend()
                ts=[True for x in subms if x.stats.npts < (ws-we)*x.stats.sampling_rate]
                nan=[True for x in subms if sum(np.isnan(x.data)) > 0]
                if sum(ts) > 0:
                    failure3.append([id,stat,net,component,"missing_vals"])
                else:
                    if sum(nan) > 0:
                        failure3.append([id,stat,net,component,"missing_vals"])
                if sortby == "event":
                    wp=wd+"data/"+id+"/"
                if sortby == "station":
                    wp=wd+"data/"+subst+"/"
                if not os.path.exists(wp):
                    os.makedirs(wp)
                if len(subms) < 3:
                    failure3.append([id,stat,net,component,"missing_vals"])
                for tr in subms:
                    trinv=inv.select(channel=tr.stats.channel,station=tr.stats.station,network=tr.stats.network,time=t)
                    sactr = SACTrace.from_obspy_trace(tr)
                    sactr.cmpaz=trinv[0][0][0].azimuth
                    sactr.cmpinc=trinv[0][0][0].dip+90 ##convert to degrees from vertical
                    sactr.stla=trinv[0][0].latitude
                    sactr.stlo=trinv[0][0].longitude
                    sactr.evdp=d
                    sactr.evlo=lon
                    sactr.evla=lat
                    sactr.mag=mag
                    sactr.a=a
                    sactr.o=o
                    sactr.stel=trinv[0][0].elevation
                    sactr.kevnm=runline2[0]
                    sactr.write(wp+id+"."+tr.stats.network+"."+tr.stats.station+"."+tr.stats.channel+".sac")
                failure.append([id,subst,nets[l],component,"completed"])
            os.remove(wd+reqname+".mseed")
            os.remove(wd+reqname)
    for l in failure3:
        failure.append(l)
    return(failure)


def dl_BH_HH(evmat,wd,stations,networks,inv,component="BH",minepi=35,maxepi=95,ws=-10,we=50,sortby="event",mod="iasp91",flo=0.03,fhi=2,mode="continue"):
    if mode == "retry":
        evtimes=np.asarray([x[1] for x in evmat])
        completed_list,failure_list=retry_download(wd,evmat,evtimes,minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi,mod=model)
        return(completed_list,failure_list)
    if mode == "all":
        print("Downloading all events...")
    if not os.path.exists(wd+"/data"):
        os.makedirs(wd+"/data")
    if mode == "continue":
        print("Continuing download...")
        skip=[]
        file = open(wd+"completed_events","a+")
        file.close()
        file = open(wd+"missing_events","a+")
        file.close()
        with open(wd+"completed_events", 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            ss=[skip.append(x) for x in reader]
        with open(wd+"missing_events", 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            ss=[skip.append(x) for x in reader]
    completed_list=[]
    failure_list=[]
    for evl in evmat:
        substations=stations
        subnet=networks
        if mode == "continue":
            subskip=np.asarray([x for x in skip if x[0] == evl[0] and (x[3] == "HH" or x[4] == "completed" or x[4] == "epi_dist")])
            subnet=[networks[x] for x in np.arange(len(substations)) if substations[x] not in subskip[:,1]]
            substations=[x for x in substations if x not in subskip[:,1]]
        rb=dl_event(evl,wd=wd,stations=substations,networks=subnet,inv=inv,component="BH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)
        blank=[completed_list.append(x) for x in rb if x[4] == "completed"]
        blank=[failure_list.append(x) for x in rb if not x[4] == "completed"]
        restat=[x[1] for x in rb if x[4] == "no_data" or x[4] == "missing_vals"]
        renet=[x[2] for x in rb if x[4] == "no_data" or x[4] == "missing_vals"]
        rh=dl_event(evl,wd=wd,stations=restat,networks=renet,inv=inv,component="HH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)
        blank=[completed_list.append(x) for x in rh if x[4] == "completed"]
        blank=[failure_list.append(x) for x in rh if not x[4] == "completed"]
    if mode == "continue":
        wm="a+"
    else:
        wm="w"
    file = open(wd+"missing_events",wm) 
    for l in failure_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()

    file = open(wd+"completed_events",wm) 
    for l in completed_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()
    return(completed_list,failure_list)

def retry_download(wd,evmat,evtimes,minepi=35,maxepi=95,ws=-10,we=50,sortby="event",mod="iasp91",flo=0.03,fhi=2):
    ###Attempt missing stations
    missing=[]
    with open(wd+"missing_stations", 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        ss=[missing.append(x) for x in reader]
    stations=[x[1] for x in missing]
    networks=[x[2] for x in missing]
##Read station metadata
    inventory,missing_stat,stations,networks=stat_meta(wd,stations,networks,evtimes=evtimes,mode="all")

    if len(stations) > 0:
        comp,fail=dl_BH_HH(evmat,wd=wd,stations=stations,networks=networks,inv=inventory,minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi,mode="continue",mod=model)

###Attempt missing events

    missing_events=[]
    with open(wd+"missing_events", 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        ss=[missing_events.append(x) for x in reader if x[4] != "epi_dist"]

    epi_events=[]
    with open(wd+"missing_events", 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        ss=[epi_events.append(x) for x in reader if x[4] == "epi_dist"]

    mevname=np.unique(np.asarray([x[0] for x in missing_events]))

    evmat=[x for x in evmat if x[0] in mevname]


    stations=np.asarray([x[1] for x in missing_events])
    unstat=np.unique(np.asarray(stations),return_index=True)[1]
    networks=np.asarray([x[2] for x in missing_events])
    inventory,missing_stat,stations,networks=stat_meta(wd,stations[unstat],networks[unstat],evtimes=evtimes,mode="all",write=False)

    missing_BH=[x for x in missing_events if x[3] == "BH"]
    missing_HH=np.asarray([x for x in missing_events if x[3] == "HH"])
    HHmerged=[x[0]+x[1]+x[2] for x in missing_HH]

    new_missing_list=[]
    for line in missing_BH:
        evl=[x for x in evmat if x[0] == line[0]][0]
        restat=[line[1]]
        renet=[line[2]]
        rt=dl_event(evl,wd=wd,stations=restat,networks=renet,inv=inventory,component="BH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)[0]
        new_missing_list.append(rt)
        if (rt[4] == 'no_data' or rt[4] == 'missing_vals') and (rt[0]+rt[1]+rt[2]) in HHmerged:
            rtt=dl_event(evl,wd=wd,stations=restat,networks=renet,inv=inventory,component="HH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)[0]
            new_missing_list.append(rtt)

    failure_list = [x for x in new_missing_list if not x == 'completed']
    completed_list = [x for x in new_missing_list if x == 'completed']

    file = open(wd+"missing_events","w") 
    for l in failure_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()
    file = open(wd+"missing_events","a+") 
    for l in epi_events:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()

    file = open(wd+"completed_events","a+") 
    for l in completed_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()
    return(completed_list,failure_list)

