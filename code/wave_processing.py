#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu June 2 12:06:18 2022

@author: fabianmk
@edited by: judiththuolberg
"""

import compress_pickle as cpkl
import arduino_logging
from datetime import datetime
import math
import numpy as np
import scipy.signal as signal


def round_to_ending_01(number_in):
    """Function used in generate_common_time_base"""
    number_out = math.floor(number_in * 10) / 10
    return number_out


def generate_common_timebase(time_base_1, time_base_2, time_base_3, time_base_4):
    """Functon used in load_data_dump to generate common time base""" 
    # find the largest common time base
    # use the ms ending in 00, as we are logging at 100Hz
    min_common_time = round_to_ending_01(max(time_base_1[0], time_base_2[0], time_base_3[0], time_base_4[0])) + 0.1
    max_common_time = round_to_ending_01(min(time_base_1[-1], time_base_2[-1], time_base_3[-1], time_base_4[-1])) - 0.1

    common_time_base = np.arange(min_common_time, max_common_time, 0.1)

    return common_time_base
    
def clockwise_plus_minus_180_to_counterclockwise_plus_minus_180(pm_180):
    return -pm_180    
    
def counterclockwise_360_to_counterclockwise_plus_minus_180(cc_360):
    if cc_360 > 180:
        return cc_360-360
    else:
        return cc_360  
    
def load_data_dump(path_to_file, show_interpolation=False, resistor_values=160.0):
    #print('dump new')
    """Load a data file, and extract all raw the data, ready to use as a dictionary"""

    # load compressed data
    with open(path_to_file, "br") as fh:
        data = cpkl.load(fh, compression="lzma")
        
    # put all the data at different stages of processing in a common dict
    dict_data = {}

    # the raw data read from the log file
    dict_data["lists_raw_data"] = {}
    dict_data["lists_raw_data"]["IMU"]=[]
    dict_data["lists_raw_data"]["gauges"] = []
    dict_data["lists_raw_data"]["meta"] = []

    dict_data["lists_raw_data"]["extraIMU_0"] = []
    dict_data["lists_raw_data"]["extraIMU_1"] = []
    
    dict_data["list_time_series"] = {}
    dict_data["list_time_series"]["extraIMU_0"]={}
    dict_data["list_time_series"]["IMU"]={}
    dict_data["list_time_series"]["extraIMU_1"]={}
    dict_data["list_time_series"]["gauges"] = {}
    dict_data["list_time_series"]["extraIMU_0"]["datetime"] = []
    dict_data["list_time_series"]["extraIMU_1"]["datetime"] = []        
    dict_data["list_time_series"]["IMU"]["datetime"]=[]    
    dict_data["list_time_series"]["gauges"]["datetime"]=[]
              

    # split in the correct categories
    for crrt_entry in data:
        # print(crrt_entry)
        crrt_datetime = crrt_entry[0]
        #print(crrt_entry[1])
        crrt_kind = crrt_entry[1]
        crrt_packet = crrt_entry[2]
        if crrt_kind == "I":
            dict_data["lists_raw_data"]["IMU"].append(crrt_packet)
            dict_data["list_time_series"]["IMU"]["datetime"].append(crrt_datetime)
        elif crrt_kind == "G":
            dict_data["lists_raw_data"]["gauges"].append(crrt_packet)
            dict_data["list_time_series"]["gauges"]["datetime"].append(crrt_datetime)
        elif crrt_kind == "9dof":
            if crrt_packet.metadata == 0:
                dict_data["lists_raw_data"]["extraIMU_0"].append(crrt_packet)
                dict_data["list_time_series"]["extraIMU_0"]["datetime"].append(crrt_datetime)
            elif crrt_packet.metadata == 1:
                dict_data["lists_raw_data"]["extraIMU_1"].append(crrt_packet)
                dict_data["list_time_series"]["extraIMU_1"]["datetime"].append(crrt_datetime)

            else:
                print("error meta value sorting")
        
        else:
            dict_data["lists_raw_data"]["meta"].append(crrt_packet)

    # produce the time series for the probe and IMU
 
    dict_data["list_time_series"]["IMU"]["accel_D"] = []
    dict_data["list_time_series"]["IMU"]["pitch"] = []
    dict_data["list_time_series"]["IMU"]["roll"] = []
    dict_data["list_time_series"]["IMU"]["yaw"] = []
    dict_data["list_time_series"]["gauges"]["gauge_ug1_meters"] = []
    dict_data["list_time_series"]["gauges"]["gauge_ug2_meters"] = []
    dict_data["list_time_series"]["gauges"]["gauge_radar1_meters"] = []
    
    dict_data["list_time_series"]["extraIMU_0"]["accel_D"] = []
    dict_data["list_time_series"]["extraIMU_0"]["pitch"] = []
    dict_data["list_time_series"]["extraIMU_0"]["roll"] = []
    dict_data["list_time_series"]["extraIMU_0"]["yaw"] = []
    dict_data["list_time_series"]["extraIMU_1"]["accel_D"] = []
    dict_data["list_time_series"]["extraIMU_1"]["pitch"] = []
    dict_data["list_time_series"]["extraIMU_1"]["roll"] = []
    dict_data["list_time_series"]["extraIMU_1"]["yaw"] = []
    dict_data["list_time_series"]["IMU"]["timestamps"]=[]
    dict_data["list_time_series"]["extraIMU_0"]["timestamps"]=[]
    dict_data["list_time_series"]["extraIMU_1"]["timestamps"]=[]
    dict_data["list_time_series"]["gauges"]["timestamps"]=[]
    
    for crrt_IMU0_packet in dict_data["lists_raw_data"]["extraIMU_0"]:
        dict_data["list_time_series"]["extraIMU_0"]["accel_D"].append(crrt_IMU0_packet.acc_D)
        dict_data["list_time_series"]["extraIMU_0"]["pitch"].append(crrt_IMU0_packet.pitch)
        dict_data["list_time_series"]["extraIMU_0"]["roll"].append(crrt_IMU0_packet.roll_)
        dict_data["list_time_series"]["extraIMU_0"]["yaw"].append(crrt_IMU0_packet.yaw__)

    for crrt_IMU1_packet in dict_data["lists_raw_data"]["extraIMU_1"]:
        dict_data["list_time_series"]["extraIMU_1"]["accel_D"].append(crrt_IMU1_packet.acc_D)
        dict_data["list_time_series"]["extraIMU_1"]["pitch"].append(crrt_IMU1_packet.pitch)
        dict_data["list_time_series"]["extraIMU_1"]["roll"].append(crrt_IMU1_packet.roll_)
        dict_data["list_time_series"]["extraIMU_1"]["yaw"].append(crrt_IMU1_packet.yaw__)

    for crrt_imu_packet in dict_data["lists_raw_data"]["IMU"]:
        dict_data["list_time_series"]["IMU"]["accel_D"].append(crrt_imu_packet.acc_D)
        dict_data["list_time_series"]["IMU"]["pitch"].append(crrt_imu_packet.pitch)
        dict_data["list_time_series"]["IMU"]["roll"].append(crrt_imu_packet.roll)
        dict_data["list_time_series"]["IMU"]["yaw"].append(crrt_imu_packet.yaw)

    for crrt_gauges_packet in dict_data["lists_raw_data"]["gauges"]:
        height_1, height_2, height_3 = \
            arduino_logging.convert_g_packet_adc_to_distances(crrt_gauges_packet, resistor_values, resistor_values, resistor_values, 12, 3.3)
        dict_data["list_time_series"]["gauges"]["gauge_ug1_meters"].append(height_1)
        dict_data["list_time_series"]["gauges"]["gauge_ug2_meters"].append(height_2)
        dict_data["list_time_series"]["gauges"]["gauge_radar1_meters"].append(height_3)
    
        

    for cnt in range(len(dict_data["list_time_series"]["IMU"]["datetime"])):
        dict_data["list_time_series"]["IMU"]["timestamps"].append(datetime.timestamp(dict_data["list_time_series"]["IMU"]["datetime"][cnt]))
    for cnt in range(len(dict_data["list_time_series"]["extraIMU_0"]["datetime"])):
        dict_data["list_time_series"]["extraIMU_0"]["timestamps"].append(datetime.timestamp(dict_data["list_time_series"]["extraIMU_0"]["datetime"][cnt]))
    for cnt in range(len(dict_data["list_time_series"]["extraIMU_1"]["datetime"])):
        dict_data["list_time_series"]["extraIMU_1"]["timestamps"].append(datetime.timestamp(dict_data["list_time_series"]["extraIMU_1"]["datetime"][cnt]))
    for cnt in range(len(dict_data["list_time_series"]["gauges"]["datetime"])):
        dict_data["list_time_series"]["gauges"]["timestamps"].append(datetime.timestamp(dict_data["list_time_series"]["gauges"]["datetime"][cnt]))

    # fix lists for sensor blackout
    imus=["IMU","extraIMU_0","extraIMU_1"]
    for imu in imus:
        if len(dict_data["list_time_series"][imu]["timestamps"]) < 1:
            dict_data["list_time_series"][imu]["timestamps"].append(dict_data["list_time_series"]["gauges"]["timestamps"][0])
            dict_data["list_time_series"][imu]["timestamps"].append(dict_data["list_time_series"]["gauges"]["timestamps"][-1])
            # print("IMU: "+imu+" failed from "+dict_data["list_time_series"]["gauges"]["datetime"][0].strftime("%H:%M")+" to "+dict_data["list_time_series"]["gauges"]["datetime"][-1].strftime("%H:%M"))
    common_time_base = generate_common_timebase(
        dict_data["list_time_series"]["IMU"]["timestamps"],
        dict_data["list_time_series"]["gauges"]["timestamps"],
        dict_data["list_time_series"]["extraIMU_1"]["timestamps"],
        dict_data["list_time_series"]["extraIMU_0"]["timestamps"]
    )

    # interpolate the time series on a common time base
    dict_data["list_time_series_interpolated"] = {}
    dict_data["list_time_series_interpolated"]["common_time_stamps"] = common_time_base
    dict_data["list_time_series_interpolated"]["common_datetime"]=[]
    for cnt in range(len(dict_data["list_time_series_interpolated"]["common_time_stamps"])):
        dict_data["list_time_series_interpolated"]["common_datetime"].append(datetime.fromtimestamp(dict_data["list_time_series_interpolated"]["common_time_stamps"][cnt]))
    dict_data["list_time_series_interpolated"]["IMU"]={}
    dict_data["list_time_series_interpolated"]["extraIMU_0"]={}
    dict_data["list_time_series_interpolated"]["extraIMU_1"]={}
    dict_data["list_time_series_interpolated"]["gauges"]={}

    
    for imu in imus:
        
        if len(dict_data["list_time_series"][imu]["timestamps"]) > 2:
            
            dict_data["list_time_series_interpolated"][imu]["accel_D"] = np.interp(
            common_time_base,dict_data["list_time_series"][imu]["timestamps"],
            dict_data["list_time_series"][imu]["accel_D"])
            
            dict_data["list_time_series_interpolated"][imu]["pitch"] = np.interp(
            common_time_base,dict_data["list_time_series"][imu]["timestamps"],
            dict_data["list_time_series"][imu]["pitch"])
            
            dict_data["list_time_series_interpolated"][imu]["roll"] = np.interp(
            common_time_base,dict_data["list_time_series"][imu]["timestamps"],
            dict_data["list_time_series"][imu]["roll"])
            
            dict_data["list_time_series_interpolated"][imu]["yaw"] = np.interp(
            common_time_base,dict_data["list_time_series"][imu]["timestamps"],
            dict_data["list_time_series"][imu]["yaw"])
            
            if imu == "extraIMU_0" or imu == "extraIMU_1":
                cnt = -1
                for i in dict_data["list_time_series_interpolated"][imu]["yaw"]:
                    cnt+=1    
                    dict_data["list_time_series_interpolated"][imu]["yaw"][cnt]=counterclockwise_360_to_counterclockwise_plus_minus_180(dict_data["list_time_series_interpolated"][imu]["yaw"][cnt])
            
            if imu == "IMU":
                cnt = -1
                for i in dict_data["list_time_series_interpolated"][imu]["yaw"]:
                    cnt+=1    
                    dict_data["list_time_series_interpolated"][imu]["yaw"][cnt]=clockwise_plus_minus_180_to_counterclockwise_plus_minus_180(dict_data["list_time_series_interpolated"][imu]["yaw"][cnt])
                
                cnt = -1    
                for i in dict_data["list_time_series_interpolated"][imu]["pitch"]:
                    cnt+=1    
                    dict_data["list_time_series_interpolated"][imu]["pitch"][cnt]=-dict_data["list_time_series_interpolated"][imu]["pitch"][cnt]
                    
                cnt = -1
                for i in dict_data["list_time_series_interpolated"][imu]["accel_D"]:
                    cnt+=1    
                    dict_data["list_time_series_interpolated"][imu]["accel_D"][cnt]=-dict_data["list_time_series_interpolated"][imu]["accel_D"][cnt]       
            
        else:

            dict_data["list_time_series_interpolated"][imu]["accel_D"]=[]
            for cnt in range(len(common_time_base)):
                dict_data["list_time_series_interpolated"][imu]["accel_D"].append(np.nan) 
            dict_data["list_time_series_interpolated"][imu]["pitch"]=dict_data["list_time_series_interpolated"][imu]["accel_D"]*1
            dict_data["list_time_series_interpolated"][imu]["roll"]=dict_data["list_time_series_interpolated"][imu]["accel_D"]*1
            dict_data["list_time_series_interpolated"][imu]["yaw"]=dict_data["list_time_series_interpolated"][imu]["accel_D"]*1
    
    
    
    dict_data["list_time_series_interpolated"]["gauges"]["gauge_ug1_meters"] = np.interp(
        common_time_base,
        dict_data["list_time_series"]["gauges"]["timestamps"],
        dict_data["list_time_series"]["gauges"]["gauge_ug1_meters"]
    )
    dict_data["list_time_series_interpolated"]["gauges"]["gauge_ug2_meters"] = np.interp(
        common_time_base,
        dict_data["list_time_series"]["gauges"]["timestamps"],
        dict_data["list_time_series"]["gauges"]["gauge_ug2_meters"]
    )
    dict_data["list_time_series_interpolated"]["gauges"]["gauge_radar1_meters"] = np.interp(
        common_time_base,
        dict_data["list_time_series"]["gauges"]["timestamps"],
        dict_data["list_time_series"]["gauges"]["gauge_radar1_meters"]
    )
    cnt = -1
    radar_mean = np.mean(dict_data["list_time_series_interpolated"]["gauges"]["gauge_radar1_meters"])
    for i in dict_data["list_time_series_interpolated"]["gauges"]["gauge_radar1_meters"]:
        cnt+=1
        radar_wrong_fluctuation = i - radar_mean
        radar_right_fluctuation = -radar_wrong_fluctuation
        radar = radar_right_fluctuation + radar_mean 
        dict_data["list_time_series_interpolated"]["gauges"]["gauge_radar1_meters"][cnt] = radar
    
    return dict_data

def fft_der_1(data,sampling_freq):
    """Take one derivative in Fourier space"""

    # calculate fft, filter, and then ifft to get heights
    ACC_SIZE = data.shape[0]

    # suppress divide by 0 warning
    np.seterr(divide='ignore')
    F = np.fft.fft(data)
    freq = np.fft.fftfreq(ACC_SIZE, d=1.0 / sampling_freq)
    weights = (1j)*(2*np.pi*freq)
    
    der_1=np.real(np.fft.ifft(weights*F))
    
    return der_1

def fft_der_2(data,sampling_freq):
    """Take doublederivative in Fourier space"""    

    # calculate fft, filter, and then ifft to get heights
    ACC_SIZE = data.shape[0]
    
    # suppress divide by 0 warning
    np.seterr(divide='ignore')
    F = np.fft.fft(data)
    freq = np.fft.fftfreq(ACC_SIZE, d=1.0 / sampling_freq)
    weights = (-1)*(2*np.pi*freq)**2
    
    der_2=np.real(np.fft.ifft(weights*F))
    
    return der_2

def fft_int_1(data,sampling_freq):
    """Take one integration in Fourier space"""
    # calculate fft, filter, and then ifft to get heights
    int_1=fft_der_1(fft_int_2(data,sampling_freq),sampling_freq)
    
    return int_1

def fft_int_2(data,sampling_freq):
    """Take double integral in Fourier space. Function used in run_you_fools"""
    ACC_SIZE = data.shape[0]
    
    # suppress divide by 0 warning
    np.seterr(divide='ignore')

    F = np.fft.fft(data)
    freq = np.fft.fftfreq(ACC_SIZE, d=1.0 / sampling_freq) 
    weights = -1.0/((2*np.pi*freq)**2)
    Ff = np.zeros_like(F)
    
    #use same cutoff frequencies as wave oscillation    
    fmax= 0.5
    fmin = 0.05     
    ind = np.argwhere(np.logical_and(freq >= fmin, freq <= fmax))
    Ff[ind] = F[ind] * weights[ind]
    int_2=np.real(np.fft.ifft(2*Ff))     
 
    return int_2

def welch_spectrum(data_in, sampling_rate=10.0, overlap_proportion=0.9, segment_duration_seconds=180):
    """Compute the power spectrum from frequency. Function used in run_you_fools"""    
    nperseg = int(segment_duration_seconds * sampling_rate)
    noverlap = int(overlap_proportion * nperseg)

    f, Pxx_den = signal.welch(data_in, sampling_rate, nperseg=nperseg, noverlap=noverlap)

    return(f, Pxx_den)

def find_index_of_fist_element_greater_than_value(array, value):
    """Function used in compute_wave_spectrum_moments"""    
    indexes_where_greater_than = np.where(array > value)[0]
    if len(indexes_where_greater_than) == 0:
        return None
    else:
        return indexes_where_greater_than[0]

def compute_wave_spectrum_moments(list_frequencies, wave_spectrum, min_freq=0.05, max_freq=0.5):
    """Compute the moments of the wave spectrum. Function used in run_you_fools"""

    min_ind = find_index_of_fist_element_greater_than_value(list_frequencies, min_freq)
    max_ind = find_index_of_fist_element_greater_than_value(list_frequencies, max_freq)

    wave_spectrum = wave_spectrum[min_ind:max_ind]
    f = list_frequencies[min_ind:max_ind]
    
    M0 = np.trapz(wave_spectrum, x=f)
    M1 = np.trapz(wave_spectrum * (f), x=f)
    M2 = np.trapz(wave_spectrum * (f**2), x=f)
    M3 = np.trapz(wave_spectrum * (f**3), x=f)
    M4 = np.trapz(wave_spectrum * (f**4), x=f)
    MM1 = np.trapz(wave_spectrum * (f**(-1)), x=f)
    MM2 = np.trapz(wave_spectrum * (f**(-2)), x=f)

    return(M0, M1, M2, M3, M4, MM1, MM2)

         
