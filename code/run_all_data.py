#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu June 2 12:06:18 2022

@author: fabianmk
@edited by: judiththuolberg
"""
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import circmean
import os
from wave_processing import * #script that loads the raw data and does wave processing (needs arduino_logging.py)

def kts_to_ms(kts):
    """convert speed in knts to meter per seconds"""
    ms = kts*1852/(60*60)
    return ms

def correct_freq_for_Doppler_effect(freq,kts,heading,wave_dir):
    """Corrects the measured frequency for the Doppler Effect"""
    g=9.81
    v_ship=kts_to_ms(kts)
    theta=wave_dir-heading
    v_o=v_ship*np.cos(np.deg2rad(theta))
    c=g/(2*np.pi*freq)
    if v_0 > 0:
        corr_freq=-(g-np.sqrt(g**(2)+(8*np.pi*v_o*g*freq)))/(4*np.pi*v_o)
    elif v_o < 0:
        if freq < abs(g/(8*np.pi*v_o)):
            corr_freq=-(g+np.sqrt(g**(2)+(8*np.pi*v_o*g*freq)))/(4*np.pi*v_o)
        else:
            corr_freq=np.nan
    return corr_freq

def load_ship_stats(filepath="/Users/judiththuolberg/Master/Additional_data/all_pos.csv"):
    """Loads the ships position, heading, wind and speed in knts from a .csv file and returns it in a dict"""
    df = pd.read_csv(filepath)
    ret_dict={}
    ret_dict["lon"]=df.lon.values
    ret_dict["lat"]=df.lat.values
    ret_dict["wind"]=df.Wind.values
    ret_dict["wind_dir"]=df["Wind dir"].values
    ret_dict["heading"]=df.Heading.values
    ret_dict["kts"]=df.Speed.values
    ret_dict["datetime"]=[]
    for timestring in df.datetime:
        date=datetime.strptime(str(timestring),"%Y-%m-%d %H:%M:%S")
        ret_dict["datetime"].append(date)
    ret_dict["datetime"]=np.array((ret_dict["datetime"]))
    return ret_dict

def load_wave_direction(filepath="/Users/judiththuolberg/Master/Additional_data/wave_direction.csv"):
    """Loads the ECWAM wave direction from a .csv file and returns it in a dict"""
    df = pd.read_csv(filepath)
    ret_dict={}
    ret_dict["model_lons"]=df.model_lons.values
    ret_dict["model_lats"]=df.model_lats.values
    ret_dict["mdir"]=df.mdir.values
    ret_dict["datetime"]=[]
    for timestring in df.datetime:
        date=datetime.strptime(str(timestring),"%Y-%m-%d %H:%M:%S")
        ret_dict["datetime"].append(date)
    ret_dict["datetime"]=np.array((ret_dict["datetime"]))
    return ret_dict

def get_wave_data_one_file(dict_data,ship_dict,wave_dict):
    """Calculates the important wave parameters from dict_data obtained from a single data file via load_data_dict(filepath), 
    and return all the relevant information on wave parameters, ship's position, wind, speed and heading"""
    
    #get data from dict
    pitch=np.array((dict_data["list_time_series_interpolated"]["IMU"]["pitch"]))
    roll=np.array((dict_data["list_time_series_interpolated"]["IMU"]["roll"]))
    date_time=np.array((dict_data["list_time_series_interpolated"]["common_datetime"]))
    accel_D=np.array((dict_data["list_time_series_interpolated"]["IMU"]["accel_D"]))
    pitch=np.deg2rad(pitch)
    roll=np.deg2rad(roll)
    ug1=np.array(dict_data["list_time_series_interpolated"]["gauges"]["gauge_ug1_meters"])
    ug2=np.array(dict_data["list_time_series_interpolated"]["gauges"]["gauge_ug2_meters"])
    radar=np.array(dict_data["list_time_series_interpolated"]["gauges"]["gauge_radar1_meters"])
    
    #get the vertical positions of the VN100 by two times integration
    sample_freq=10
    g=9.81
    z_accel=accel_D-g
    z_pos=fft_int_2(z_accel,sample_freq)
    
    #due to Fourier transformations the data is cut off in beginning and end
    data_len=pitch.shape[0]
    cutoff=data_len//10
    date_time=date_time[cutoff:-cutoff]
    pitch=pitch[cutoff:-cutoff]
    roll=roll[cutoff:-cutoff]
    z_pos=z_pos[cutoff:-cutoff]
    ug1=ug1[cutoff:-cutoff]
    ug2=ug2[cutoff:-cutoff]
    radar=radar[cutoff:-cutoff]  
     
    #cut off unrealistic measurements
    cut_off_height = 15.8
    ug1[np.where(ug1>cut_off_height)] = 0
    ug2[np.where(ug2>cut_off_height)] = 0
    radar[np.where(radar>cut_off_height)] = 0
    
    #the water suface elevation WH_ossc is computed
    WH_ug1=ug1*np.cos(pitch)*np.cos(roll)-z_pos
    WH_mean_ug1=np.mean(WH_ug1)    
    WH_ossc_ug1=WH_mean_ug1-WH_ug1
    
    WH_ug2=ug2*np.cos(pitch)*np.cos(roll)-z_pos
    WH_mean_ug2=np.mean(WH_ug2)   
    WH_ossc_ug2=WH_mean_ug2-WH_ug2
    
    WH_radar=radar*np.cos(pitch)*np.cos(roll)-z_pos
    WH_mean_radar=np.mean(WH_radar)  
    WH_ossc_radar=WH_mean_radar-WH_radar
    
    #significant wave heights SWH are computed from standard deviation
    SWH_ug1=4*np.std(WH_ossc_ug1)
    SWH_ug2=4*np.std(WH_ossc_ug2)    
    SWH_radar=4*np.std(WH_ossc_radar)
   
    #maximum wave heights are computed manually by downcross definition
    WH_ug1s=[]
    index=[]
    for cnt in range(WH_ossc_ug1.shape[0]-1):
        if (WH_ossc_ug1[cnt]>=0 and WH_ossc_ug1[cnt+1]<0):
            index.append(cnt)

    for cnt in range(len(index)-1):
        subdata=WH_ossc_ug1[index[cnt]:index[cnt+1]]*1
        top=np.max(subdata)
        low=np.min(subdata)
        WH_ug1s.append(top-low)

    WH_ug1s=np.array((WH_ug1s))
    if WH_ug1s.shape[0]>0:
        Hs_ug1_manual=np.max(WH_ug1s)
    else:
        Hs_ug1_manual=np.nan
    
    WH_ug2s=[]
    index=[]
    for cnt in range(WH_ossc_ug2.shape[0]-1):
        if (WH_ossc_ug2[cnt]>=0 and WH_ossc_ug2[cnt+1]<0):
            index.append(cnt)
            
    for cnt in range(len(index)-1):
        subdata=WH_ossc_ug2[index[cnt]:index[cnt+1]]*1
        top=np.max(subdata)
        low=np.min(subdata)
        WH_ug2s.append(top-low)

    WH_ug2s=np.array((WH_ug2s))
    if WH_ug2s.shape[0]>0:
        Hs_ug2_manual=np.max(WH_ug2s)
    else:
        Hs_ug2_manual=np.nan    

    WH_radars=[]
    index=[]
    for cnt in range(WH_ossc_radar.shape[0]-1):
        if (WH_ossc_radar[cnt]>=0 and WH_ossc_radar[cnt+1]<0):
            index.append(cnt)
            
    for cnt in range(len(index)-1):
        subdata=WH_ossc_radar[index[cnt]:index[cnt+1]]*1
        top=np.max(subdata)
        low=np.min(subdata)
        WH_radars.append(top-low)
        
    WH_radars=np.array((WH_radars))
    if WH_radars.shape[0]>0:
        Hs_radar_manual=np.max(WH_radars)
    else:
        Hs_radar_manual=np.nan
    
    #calculating one value from the additional data within the 30minutes dataset with minute resolution
    t_start=date_time[0]
    t_end=date_time[-1]
    kts_array=ship_dict["kts"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]
    heading_array=ship_dict["heading"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]
    wind_dir_array=ship_dict["wind_dir"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]
    wind_array=ship_dict["wind"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]
    lon_array=ship_dict["lon"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]
    lat_array=ship_dict["lat"][np.where(((ship_dict["datetime"]>t_start)&(ship_dict["datetime"]<t_end)))]

    kts=np.nanmean(kts_array)
    wind=np.nanmean(wind_array)
    lon=np.nanmean(lon_array)
    lat=np.nanmean(lat_array)
    heading=circmean(heading_array,high=360,low=0)   
    wind_dir=circmean(wind_dir_array,high=360,low=0)

    #extracting one value of the wave direction within the dataset with 60min resolution
    delta_t_start=np.abs(wave_dict["datetime"]-t_start)
    closest_t_start=np.min(delta_t_start)
    delta_t_end=np.abs(wave_dict["datetime"]-t_end)
    closest_t_end=np.min(delta_t_end)
    if closest_t_start<=closest_t_end:
        ind_closest_t=np.argmin(delta_t_start)
        wave_dir=wave_dict["mdir"][ind_closest_t]
    else:
        ind_closest_t=np.argmin(delta_t_end)
        wave_dir=wave_dict["mdir"][ind_closest_t]
    
    #avoid dividing with zero for doppler correction    
    if wave_dir == 0:
        wave_dir +=0.1    
    
    if heading == 0:
        heading+=0.1
    
    if kts == 0:
        kts += 0.1
     
    #segment_duration for the welch spectrum, usually seg_secs = 180 is used, but if data is missing, a lower value is used to make sure seg_secs is smaller than nperseg
    dt_sec=(t_end-t_start).seconds
    times_180=dt_sec//180 
    if times_180 >= 3:
        seg_secs=180
    else:
        seg_secs=dt_sec/2
    
    #calculate wave spectrum with the welch method
    freqs_ug1,Pxx_ug1=welch_spectrum(WH_ossc_ug1,segment_duration_seconds=seg_secs)
    freqs_ug2,Pxx_ug2=welch_spectrum(WH_ossc_ug2,segment_duration_seconds=seg_secs)
    freqs_radar,Pxx_radar=welch_spectrum(WH_ossc_radar,segment_duration_seconds=seg_secs)

    #retain only frequencies relevant for ocean waves
    fmin = 0.05
    fmax = 0.5

    Pxx_ug1=Pxx_ug1[np.where((freqs_ug1 >= fmin)&(freqs_ug1<= fmax))]
    Pxx_ug2=Pxx_ug2[np.where((freqs_ug2 >= fmin)&(freqs_ug2<= fmax))]
    Pxx_radar=Pxx_radar[np.where((freqs_radar >= fmin)&(freqs_radar<= fmax))]
    
    freqs_ug1=freqs_ug1[np.where((freqs_ug1 >= fmin)&(freqs_ug1<= fmax))]
    freqs_ug2=freqs_ug2[np.where((freqs_ug2 >= fmin)&(freqs_ug2<= fmax))]
    freqs_radar=freqs_radar[np.where((freqs_radar >= fmin)&(freqs_radar<= fmax))]

    #calculate wave spectrum for the Doppler shifted frequencies
    Pxx_DoppShift_ug1=Pxx_ug1*1
    Pxx_DoppShift_ug2=Pxx_ug2*1
    Pxx_DoppShift_radar=Pxx_radar*1
    
    freqs_DoppShift_ug1=[]
    freqs_DoppShift_ug2=[]
    freqs_DoppShift_radar=[]
    
    for freq in freqs_ug1:
        freq_corr=correct_freq_for_Doppler_effect(freq,kts,heading,wave_dir)
        freqs_DoppShift_ug1.append(freq_corr)
    
    for freq in freqs_ug2:
        freq_corr=correct_freq_for_Doppler_effect(freq,kts,heading,wave_dir)
        freqs_DoppShift_ug2.append(freq_corr)
              
    for freq in freqs_radar:
        freq_corr=correct_freq_for_Doppler_effect(freq,kts,heading,wave_dir)
        freqs_DoppShift_radar.append(freq_corr)
    
    #keep only non-nan values    
    freqs_DoppShift_ug1=np.array((freqs_DoppShift_ug1))
    Pxx_DoppShift_ug1=Pxx_DoppShift_ug1[np.isfinite(freqs_DoppShift_ug1)]
    freqs_DoppShift_ug1=freqs_DoppShift_ug1[np.isfinite(freqs_DoppShift_ug1)]
    Pxx_DoppShift_ug1=Pxx_DoppShift_ug1[np.where((freqs_DoppShift_ug1 >= fmin)&(freqs_DoppShift_ug1<= fmax))]
    freqs_DoppShift_ug1=freqs_DoppShift_ug1[np.where((freqs_DoppShift_ug1 >= fmin)&(freqs_DoppShift_ug1<= fmax))]
    
    freqs_DoppShift_ug2=np.array((freqs_DoppShift_ug2))
    Pxx_DoppShift_ug2=Pxx_DoppShift_ug2[np.isfinite(freqs_DoppShift_ug2)]
    freqs_DoppShift_ug2=freqs_DoppShift_ug2[np.isfinite(freqs_DoppShift_ug2)]
    Pxx_DoppShift_ug2=Pxx_DoppShift_ug2[np.where((freqs_DoppShift_ug2 >= fmin)&(freqs_DoppShift_ug2<= fmax))]
    freqs_DoppShift_ug2=freqs_DoppShift_ug2[np.where((freqs_DoppShift_ug2 >= fmin)&(freqs_DoppShift_ug2<= fmax))]

    freqs_DoppShift_radar=np.array((freqs_DoppShift_radar)) 
    Pxx_DoppShift_radars=Pxx_DoppShift_radar[np.isfinite(freqs_DoppShift_radar)]
    freqs_DoppShift_radar=freqs_DoppShift_radar[np.isfinite(freqs_DoppShift_radar)]
    Pxx_DoppShift_radar=Pxx_DoppShift_radar[np.where((freqs_DoppShift_radar >= fmin)&(freqs_DoppShift_radar<= fmax))]
    freqs_DoppShift_radar=freqs_DoppShift_radar[np.where((freqs_DoppShift_radar >= fmin)&(freqs_DoppShift_radar<= fmax))]
    
    #calculate spectral moments and wave properties
    M0_ug1, M1_ug1, M2_ug1, M3_ug1, M4_ug1, MM1_ug1, MM2_ug1 = compute_wave_spectrum_moments(freqs_ug1,Pxx_ug1)
    Hs_ug1= np.sqrt(M0_ug1) * 4.0
    Tp_ug1=1/(freqs_ug1[np.nanargmax(Pxx_ug1)])
    Tme_ug1=MM1_ug1/M0_ug1
    Tf_ug1=M0_ug1/M1_ug1
    Tzc_ug1=np.sqrt(M0_ug1/M2_ug1)
    
    M0_ug2, M1_ug2, M2_ug2, M3_ug2, M4_ug2, MM1_ug2, MM2_ug2 = compute_wave_spectrum_moments(freqs_ug2,Pxx_ug2)
    Hs_ug2= np.sqrt(M0_ug2) * 4.0
    Tp_ug2=1/(freqs_ug2[np.nanargmax(Pxx_ug2)])
    Tme_ug2=MM1_ug2/M0_ug2
    Tf_ug2=M0_ug2/M1_ug2
    Tzc_ug2=np.sqrt(M0_ug2/M2_ug2)
    
    M0_radar, M1_radar, M2_radar, M3_radar, M4_radar, MM1_radar, MM2_radar = compute_wave_spectrum_moments(freqs_radar,Pxx_radar)
    Hs_radar= np.sqrt(M0_radar) * 4.0
    Tp_radar=1/(freqs_radar[np.nanargmax(Pxx_radar)])
    Tme_radar=MM1_radar/M0_radar
    Tf_radar=M0_radar/M1_radar
    Tzc_radar=np.sqrt(M0_radar/M2_radar)
    
    #calculate Dopller shifted spectral moments and wave properties
    if freqs_DoppShift_ug1.shape[0]>0:
        M0_DoppShift_ug1, M1_DoppShift_ug1, M2_DoppShift_ug1, M3_DoppShift_ug1, M4_DoppShift_ug1, MM1_DoppShift_ug1, MM2_DoppShift_ug1 = compute_wave_spectrum_moments(freqs_DoppShift_ug1,Pxx_DoppShift_ug1)
        Hs_DoppShift_ug1= np.sqrt(M0_DoppShift_ug1) * 4.0
        Tp_DoppShift_ug1=1/(freqs_DoppShift_ug1[np.nanargmax(Pxx_DoppShift_ug1)])
        Tme_DoppShift_ug1=MM1_DoppShift_ug1/M0_DoppShift_ug1   
        Tf_DoppShift_ug1=M0_DoppShift_ug1/M1_DoppShift_ug1
        Tzc_DoppShift_ug1=np.sqrt(M0_DoppShift_ug1/M2_DoppShift_ug1)
    
        M0_DoppShift_ug2, M1_DoppShift_ug2, M2_DoppShift_ug2, M3_DoppShift_ug2, M4_DoppShift_ug2, MM1_DoppShift_ug2, MM2_DoppShift_ug2 = compute_wave_spectrum_moments(freqs_DoppShift_ug2,Pxx_DoppShift_ug2)
        Hs_DoppShift_ug2= np.sqrt(M0_DoppShift_ug2) * 4.0
        Tp_DoppShift_ug2=1/(freqs_DoppShift_ug2[np.nanargmax(Pxx_DoppShift_ug2)])
        Tme_DoppShift_ug2=MM1_DoppShift_ug2/M0_DoppShift_ug2    
        Tf_DoppShift_ug2=M0_DoppShift_ug2/M1_DoppShift_ug2
        Tzc_DoppShift_ug2=np.sqrt(M0_DoppShift_ug2/M2_DoppShift_ug2)
 
        M0_DoppShift_radar, M1_DoppShift_radar, M2_DoppShift_radar, M3_DoppShift_radar, M4_DoppShift_radar, MM1_DoppShift_radar, MM2_DoppShift_radar = compute_wave_spectrum_moments(freqs_DoppShift_radar,Pxx_DoppShift_radar)
        Hs_DoppShift_radar= np.sqrt(M0_DoppShift_radar) * 4.0
        Tp_DoppShift_radar=1/(freqs_DoppShift_radar[np.nanargmax(Pxx_DoppShift_radar)])
        Tme_DoppShift_radar=MM1_DoppShift_radar/M0_DoppShift_radar    
        Tf_DoppShift_radar=M0_DoppShift_radar/M1_DoppShift_radar
        Tzc_DoppShift_radar=np.sqrt(M0_DoppShift_radar/M2_DoppShift_radar)
     
    else:
        Hs_DoppShift_ug1 = np.nan
        Tp_DoppShift_ug1 = np.nan
        Tme_DoppShift_ug1 = np.nan
        Tf_DoppShift_ug1 = np.nan
        Tzc_DoppShift_ug1 = np.nan
        
        Hs_DoppShift_ug2 = np.nan
        Tp_DoppShift_ug2 = np.nan
        Tme_DoppShift_ug2 = np.nan
        Tf_DoppShift_ug2 = np.nan
        Tzc_DoppShift_ug2 = np.nan
        
        Hs_DoppShift_radar = np.nan
        Tp_DoppShift_radar = np.nan
        Tme_DoppShift_radar = np.nan
        Tf_DoppShift_radar = np.nan
        Tzc_DoppShift_radar = np.nan
        
    return SWH_ug1,SWH_ug2,SWH_radar,Hs_ug1_manual,Hs_ug2_manual,Hs_radar_manual,Hs_ug1,Hs_DoppShift_ug1,Tp_ug1,Tp_DoppShift_ug1,Tme_ug1,Tme_DoppShift_ug1,Tf_ug1,Tf_DoppShift_ug1,Tzc_ug1,Tzc_DoppShift_ug1,Hs_ug2,Hs_DoppShift_ug2,Tp_ug2,Tp_DoppShift_ug2,Tme_ug2,Tme_DoppShift_ug2,Tf_ug2,Tf_DoppShift_ug2,Tzc_ug2,Tzc_DoppShift_ug2,Hs_radar,Hs_DoppShift_radar,Tp_radar,Tp_DoppShift_radar,Tme_radar,Tme_DoppShift_radar,Tf_radar,Tf_DoppShift_radar,Tzc_radar,Tzc_DoppShift_radar,heading,kts,wave_dir,wind_dir,wind,lon,lat #,SWH_ug1_scaled,SWH_ug2_scaled,SWH_radar_scaled

def get_wave_data_all_files():
    """Goes through folders and files in base_path, computes the parameters with get_wave_data_one_file()
    and gathers all the relevant information on wave parameters, ship's position, wind, speed and heading in one dict"""
    
    base_path = "/Users/judiththuolberg/Master/all_data/test/2021/10/22"    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
    ship_dict=load_ship_stats()
    wave_dict=load_wave_direction()
    
    SWH_ug1=[]
    SWH_ug2=[]
    SWH_radar=[]    
    Hs_ug1_manual=[]
    Hs_ug2_manual=[]
    Hs_radar_manual=[]
    Hs_ug1=[]
    Hs_ug2=[]
    Hs_radar=[]
    Hs_DoppShift_ug1=[]
    Hs_DoppShift_ug2=[]
    Hs_DoppShift_radar=[]
    Tp_ug1=[]
    Tp_DoppShift_ug1=[]
    Tme_ug1=[]
    Tme_DoppShift_ug1=[]
    Tf_ug1=[]
    Tf_DoppShift_ug1=[]
    Tzc_ug1=[]
    Tzc_DoppShift_ug1=[]
    Tp_ug2=[]
    Tp_DoppShift_ug2=[]
    Tme_ug2=[]
    Tme_DoppShift_ug2=[]
    Tf_ug2=[]
    Tf_DoppShift_ug2=[]
    Tzc_ug2=[]
    Tzc_DoppShift_ug2=[]
    Tp_radar=[]
    Tp_DoppShift_radar=[]
    Tme_radar=[]
    Tme_DoppShift_radar=[]
    Tf_radar=[]
    Tf_DoppShift_radar=[]
    Tzc_radar=[]
    Tzc_DoppShift_radar=[]    
    date_time=[]
    heading=[]
    kts=[]
    wave_dir=[]
    wind_dir=[]
    wind=[]
    lon=[]
    lat=[]

    dir_cnt=0
    for (root,dirs,files) in os.walk(base_path):
        dirs.sort()
        files.sort()
        dir_cnt+=1
        file_cnt=0
    
        for file_name in files:
            if not(file_name.endswith(".lzma")):
                continue
            file_cnt+=1
            print('\x1b[1K' ,end="\r")
            print("folder counter: ",dir_cnt," file counter: ",file_cnt, end="\r")
            file_path=root+"/"+file_name
            dict_data=load_data_dump(file_path)

            curr_SWH_ug1,curr_SWH_ug2,curr_SWH_radar,curr_Hs_ug1_manual,curr_Hs_ug2_manual,curr_Hs_radar_manual,curr_Hs_ug1,curr_Hs_DoppShift_ug1,curr_Tp_ug1,curr_Tp_DoppShift_ug1,curr_Tme_ug1,curr_Tme_DoppShift_ug1,curr_Tf_ug1,curr_Tf_DoppShift_ug1,curr_Tzc_ug1,curr_Tzc_DoppShift_ug1,curr_Hs_ug2,curr_Hs_DoppShift_ug2,curr_Tp_ug2,curr_Tp_DoppShift_ug2,curr_Tme_ug2,curr_Tme_DoppShift_ug2,curr_Tf_ug2,curr_Tf_DoppShift_ug2,curr_Tzc_ug2,curr_Tzc_DoppShift_ug2,curr_Hs_radar,curr_Hs_DoppShift_radar,curr_Tp_radar,curr_Tp_DoppShift_radar,curr_Tme_radar,curr_Tme_DoppShift_radar,curr_Tf_radar,curr_Tf_DoppShift_radar,curr_Tzc_radar,curr_Tzc_DoppShift_radar,curr_heading,curr_kts,curr_wave_dir,curr_wind_dir,curr_wind,curr_lon,curr_lat = get_wave_data_one_file(dict_data,ship_dict,wave_dict) #curr_SWH_ug1_scaled,curr_SWH_ug2_scaled,curr_SWH_radar_scaled
                
            SWH_ug1.append(curr_SWH_ug1)
            SWH_ug2.append(curr_SWH_ug2)
            SWH_radar.append(curr_SWH_radar)
            Hs_ug1_manual.append(curr_Hs_ug1_manual)
            Hs_ug2_manual.append(curr_Hs_ug2_manual)
            Hs_radar_manual.append(curr_Hs_radar_manual)
            
            Hs_ug1.append(curr_Hs_ug1)
            Hs_DoppShift_ug1.append(curr_Hs_DoppShift_ug1)
            Tp_ug1.append(curr_Tp_ug1)
            Tp_DoppShift_ug1.append(curr_Tp_DoppShift_ug1)
            Tme_ug1.append(curr_Tme_ug1)
            Tme_DoppShift_ug1.append(curr_Tme_DoppShift_ug1)
            Tf_ug1.append(curr_Tf_ug1)
            Tf_DoppShift_ug1.append(curr_Tf_DoppShift_ug1)
            Tzc_ug1.append(curr_Tzc_ug1)
            Tzc_DoppShift_ug1.append(curr_Tzc_DoppShift_ug1)
            
            Hs_ug2.append(curr_Hs_ug2)
            Hs_DoppShift_ug2.append(curr_Hs_DoppShift_ug2)
            Tp_ug2.append(curr_Tp_ug2)
            Tp_DoppShift_ug2.append(curr_Tp_DoppShift_ug2)
            Tme_ug2.append(curr_Tme_ug2)
            Tme_DoppShift_ug2.append(curr_Tme_DoppShift_ug2)
            Tf_ug2.append(curr_Tf_ug2)
            Tf_DoppShift_ug2.append(curr_Tf_DoppShift_ug2)
            Tzc_ug2.append(curr_Tzc_ug2)
            Tzc_DoppShift_ug2.append(curr_Tzc_DoppShift_ug2)
            
            Hs_radar.append(curr_Hs_radar)
            Hs_DoppShift_radar.append(curr_Hs_DoppShift_radar)
            Tp_radar.append(curr_Tp_radar)
            Tp_DoppShift_radar.append(curr_Tp_DoppShift_radar)
            Tme_radar.append(curr_Tme_radar)
            Tme_DoppShift_radar.append(curr_Tme_DoppShift_radar)
            Tf_radar.append(curr_Tf_radar)
            Tf_DoppShift_radar.append(curr_Tf_DoppShift_radar)
            Tzc_radar.append(curr_Tzc_radar)
            Tzc_DoppShift_radar.append(curr_Tzc_DoppShift_radar)

            heading.append(curr_heading)
            kts.append(curr_kts)
            wave_dir.append(curr_wave_dir)
            wind_dir.append(curr_wind_dir)
            wind.append(curr_wind)
            lon.append(curr_lon)
            lat.append(curr_lat)
            date_time.append(dict_data["list_time_series_interpolated"]["common_datetime"][0])
    
    SWH_ug1=np.array((SWH_ug1))
    SWH_ug2=np.array((SWH_ug2))
    SWH_radar=np.array((SWH_radar))
    Hs_ug1_manual=np.array((Hs_ug1_manual))
    Hs_ug2_manual=np.array((Hs_ug2_manual))
    Hs_radar_manual=np.array((Hs_radar_manual))
    
    Hs_ug1=np.array((Hs_ug1))
    Hs_DoppShift_ug1=np.array((Hs_DoppShift_ug1))
    Tp_ug1=np.array((Tp_ug1))
    Tp_DoppShift_ug1=np.array((Tp_DoppShift_ug1))
    Tme_ug1=np.array((Tme_ug1))
    Tme_DoppShift_ug1=np.array((Tme_DoppShift_ug1))
    Tf_ug1=np.array((Tf_ug1))
    Tf_DoppShift_ug1=np.array((Tf_DoppShift_ug1))
    Tzc_ug1=np.array((Tzc_ug1))
    Tzc_DoppShift_ug1=np.array((Tzc_DoppShift_ug1))
    
    Hs_ug2=np.array((Hs_ug2))
    Hs_DoppShift_ug2=np.array((Hs_DoppShift_ug2))
    Tp_ug2=np.array((Tp_ug2))
    Tp_DoppShift_ug2=np.array((Tp_DoppShift_ug2))
    Tme_ug2=np.array((Tme_ug2))
    Tme_DoppShift_ug2=np.array((Tme_DoppShift_ug2))
    Tf_ug2=np.array((Tf_ug2))
    Tf_DoppShift_ug2=np.array((Tf_DoppShift_ug2))
    Tzc_ug2=np.array((Tzc_ug2))
    Tzc_DoppShift_ug2=np.array((Tzc_DoppShift_ug2))
    
    Hs_radar=np.array((Hs_radar))
    Hs_DoppShift_radar=np.array((Hs_DoppShift_radar))
    Tp_radar=np.array((Tp_radar))
    Tp_DoppShift_radar=np.array((Tp_DoppShift_radar))
    Tme_radar=np.array((Tme_radar))
    Tme_DoppShift_radar=np.array((Tme_DoppShift_radar))
    Tf_radar=np.array((Tf_radar))
    Tf_DoppShift_radar=np.array((Tf_DoppShift_radar))
    Tzc_radar=np.array((Tzc_radar))
    Tzc_DoppShift_radar=np.array((Tzc_DoppShift_radar))

    heading=np.array((heading))
    kts=np.array((kts))
    wave_dir=np.array((wave_dir))
    wind_dir=np.array((wind_dir))
    wind=np.array((wind))
    lon=np.array((lon))
    lat=np.array((lat))    
    date_time=np.array((date_time))
    
    ret_dict={}
    ret_dict["datetime"]=date_time
    ret_dict["heading"]=heading
    ret_dict["wave_dir"]=wave_dir
    ret_dict["wind_dir"]=wind_dir
    ret_dict["kts"]=kts
    ret_dict["wind"]=wind
    ret_dict["lon"]=lon
    ret_dict["lat"]=lat
    ret_dict["ug1"]={}
    ret_dict["ug2"]={}
    ret_dict["radar"]={}
    
    ret_dict["ug1"]["Hs"]={}
    ret_dict["ug1"]["Hs"]["SWH"]=SWH_ug1
    ret_dict["ug1"]["Hs"]["H_1/3"]=Hs_ug1_manual
    ret_dict["ug1"]["Hs"]["Hs"]=Hs_ug1
    ret_dict["ug1"]["Hs"]["Hs_DoppShift"]=Hs_DoppShift_ug1
    ret_dict["ug1"]["Tp"]={}
    ret_dict["ug1"]["Tp"]["Tp"]=Tp_ug1
    ret_dict["ug1"]["Tp"]["Tp_DoppShift"]=Tp_DoppShift_ug1
    ret_dict["ug1"]["Tme"]={}
    ret_dict["ug1"]["Tme"]["Tme"]=Tme_ug1
    ret_dict["ug1"]["Tme"]["Tme_DoppShift"]=Tme_DoppShift_ug1
    ret_dict["ug1"]["Tf"]={}
    ret_dict["ug1"]["Tf"]["Tf"]=Tf_ug1
    ret_dict["ug1"]["Tf"]["Tf_DoppShift"]=Tf_DoppShift_ug1
    ret_dict["ug1"]["Tzc"]={}
    ret_dict["ug1"]["Tzc"]["Tzc"]=Tzc_ug1
    ret_dict["ug1"]["Tzc"]["Tzc_DoppShift"]=Tzc_DoppShift_ug1
    
    ret_dict["ug2"]["Hs"]={}
    ret_dict["ug2"]["Hs"]["SWH"]=SWH_ug2
    ret_dict["ug2"]["Hs"]["H_1/3"]=Hs_ug2_manual
    ret_dict["ug2"]["Hs"]["Hs"]=Hs_ug2
    ret_dict["ug2"]["Hs"]["Hs_DoppShift"]=Hs_DoppShift_ug2
    ret_dict["ug2"]["Tp"]={}    
    ret_dict["ug2"]["Tp"]["Tp"]=Tp_ug2
    ret_dict["ug2"]["Tp"]["Tp_DoppShift"]=Tp_DoppShift_ug2
    ret_dict["ug2"]["Tme"]={}
    ret_dict["ug2"]["Tme"]["Tme"]=Tme_ug2
    ret_dict["ug2"]["Tme"]["Tme_DoppShift"]=Tme_DoppShift_ug2
    ret_dict["ug2"]["Tf"]={}
    ret_dict["ug2"]["Tf"]["Tf"]=Tf_ug2
    ret_dict["ug2"]["Tf"]["Tf_DoppShift"]=Tf_DoppShift_ug2
    ret_dict["ug2"]["Tzc"]={}
    ret_dict["ug2"]["Tzc"]["Tzc"]=Tzc_ug2
    ret_dict["ug2"]["Tzc"]["Tzc_DoppShift"]=Tzc_DoppShift_ug2
    
    ret_dict["radar"]["Hs"]={}
    ret_dict["radar"]["Hs"]["SWH"]=SWH_radar
    ret_dict["radar"]["Hs"]["H_1/3"]=Hs_radar_manual
    ret_dict["radar"]["Hs"]["Hs"]=Hs_radar
    ret_dict["radar"]["Hs"]["Hs_DoppShift"]=Hs_DoppShift_radar
    ret_dict["radar"]["Tp"]={}    
    ret_dict["radar"]["Tp"]["Tp"]=Tp_radar
    ret_dict["radar"]["Tp"]["Tp_DoppShift"]=Tp_DoppShift_radar
    ret_dict["radar"]["Tme"]={}
    ret_dict["radar"]["Tme"]["Tme"]=Tme_radar
    ret_dict["radar"]["Tme"]["Tme_DoppShift"]=Tme_DoppShift_radar
    ret_dict["radar"]["Tf"]={}
    ret_dict["radar"]["Tf"]["Tf"]=Tf_radar
    ret_dict["radar"]["Tf"]["Tf_DoppShift"]=Tf_DoppShift_radar
    ret_dict["radar"]["Tzc"]={}
    ret_dict["radar"]["Tzc"]["Tzc"]=Tzc_radar
    ret_dict["radar"]["Tzc"]["Tzc_DoppShift"]=Tzc_DoppShift_radar

    return ret_dict
