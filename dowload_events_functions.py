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


##Main download function

def dl_event(evline,wd,stations,inv,component="BH",minepi=30,maxepi=95,ws=-10,we=50,sortby="event",mod="iasp91",flo=0.03,fhi=2):
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
        #subinv=inv.select(station=stations[j],time=t,channel="BH*")
        subinv=inv.select(station=stations[j],time=t,channel=component+"*")
        if len(subinv) == 0:
            failure.append([id,stations[j],networks[j],component,"no_data"])
        else:
            net=subinv[0].code
            stat=subinv[0][0].code
            slat=subinv[0][0].latitude
            slon=subinv[0][0].longitude
            epi=locations2degrees(lat,lon,slat,slon)
            if epi < minepi or epi > maxepi:
                failure.append([id,stations[j],networks[j],component,"epi_dist"])
            else:
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


def dl_BH_HH(evmat,wd,stations,inv,component="BH",minepi=35,maxepi=95,ws=-10,we=50,sortby="event",mod="iasp91",flo=0.03,fhi=2,mode="continue"):
    if mode == "all":
        print("Downloading all events...")
    if not os.path.exists(wd+"/data"):
        os.makedirs(wd+"/data")
    if mode == "continue":
        print("Continuing download...")
        skip=[]
        file = open(wd+"missing_stations","a+")
        file.close()
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
        with open(wd+"missing_stations", 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            ss=np.asarray([x for x in reader])
        stations=[x for x in stations if x not in ss[:,1]]
    completed_list=[]
    failure_list=[]
    for evl in evmat:
        substations=stations
        if mode == "continue":
            subskip=np.asarray([x for x in skip if x[0] == evl[0] and (x[3] == "HH" or x[4] == "completed")])
            substations=[x for x in substations if x not in subskip[:,1]]
        rb=dl_event(evl,wd=wd,stations=substations,inv=inv,component="BH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)
        blank=[completed_list.append(x) for x in rb if x[4] == "completed"]
        blank=[failure_list.append(x) for x in rb if not x[4] == "completed"]
        restat=[x[1] for x in rb if not x[4] == "completed"]
        rh=dl_event(evl,wd=wd,stations=restat,inv=inv,component="HH",minepi=minepi,maxepi=maxepi,ws=ws,we=we,sortby=sortby,flo=flo,fhi=fhi)
        blank=[completed_list.append(x) for x in rh if x[4] == "completed"]
        blank=[failure_list.append(x) for x in rh if not x[4] == "completed"]
    if mode == "continue":
        wm="a+"
    else:
        wm="w"
    file = open(wd+"missing_stations",wm) 
    for l in missing_stat:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()

    file = open(wd+"missing_events",wm) 
    for l in failure_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()

    file = open(wd+"completed_events",wm) 
    for l in completed_list:
        file.write(pasteR(l,sep=",")+"\n")
    file.close()
    return(completed_list,failure_list)



