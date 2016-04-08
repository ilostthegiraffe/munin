#!/usr/bin/env python

#
# Script to get SMART DATA from a FreeBSD based system (ie FreeNAS).  Write to csv.  Can be called from munin plugin SSH__FreeNAS_HDDTemp
#

'''Import SATA SMART DATA'''

#import handy commands
import os
import sys
import re
import time
import datetime
import csv


smart_device_table=[]
smart_devices = []
current_unix_time = int(time.time())
#just to keep it quiet in testing

def fnGetSmartData():
    smart_device_info=[]

    #get list of devices in system
    smart_list_devices_raw=os.popen("smartctl --scan").read().split('\n')
    #print smart_list_devices_raw
    #
    for index, line in enumerate(smart_list_devices_raw):
        line=line.split(' ')
        if index <len(smart_list_devices_raw)-1:
            #print "index:", index, "line", line[0],line[5]
            append_data = line[0],line[5]
            smart_devices.append(append_data)


    #get data for each device detected
    #
    #SMART 5 Reallocated_Sector_Count.
    #SMART 187eported_Uncorrectable_Errors.
    #SMART 188Command_Timeout.
    #SMART 197 urrent_Pending_Sector_Count.
    #SMART 198 Offline_Uncorrectable.



    #get name, serial number etc
    for slashdevid in smart_devices:
        device_model = "-1"
        device_serial = "-2"
        device_health = "-3"
        device_firmware_version = "-4"
        device_capacity = "-5"
        device_hrs = "-6"
        device_tempC = "-7"
        device_sscount = "-8"
        device_5reallocate = "-05"
        device_198OfflineUncorrectable = "-198"
        device_187ReportedUncorrectableErrors = "-187"
        device_188CommandTimeout = "-188"
        device_197CurrentPendingSector = "-197"

        #print "slash", slashdevid
        #print "slash0", slashdevid[0]
        slashid=slashdevid[0]
        #add in slashid rather tahn ada1 to make this work!
        smart_device_data=os.popen("smartctl -a " + slashdevid[0] ).read().split('\n')

        #print "raw", smart_device_data


        #print "rawline:", smart_device_name
        #scan through smart_device_data for name field
        for index, item in enumerate(smart_device_data):
            #print 'raw item', item
            if "Device Model" in item:
                device_model = item[18:]
                #print "device_model", device_model


            if "Firmware Version:" in item:
                device_firmware_version = item[17:]
                #print "device firmware:", device_firmware_version


            if "Serial" in item:
                device_serial = item[17:]
                #print "device serial:", device_serial


            if "SMART overall-health self-assessment" in item:
                device_health = item.split (":")
                device_health = device_health[1]
                #print "Smart health", device_health


            if "User Capacity" in item:
                device_capacity = item.split("[")
                device_capacity =  device_capacity[1].replace("]", "")
                #print "device_capacity", device_capacity


            if "Power_On_Hours" in item:
                device_hrs = item.split(" ")
                device_hrs = device_hrs[43:][0]
                #print "Power on hrs", device_hrs


            if "4 Start_Stop_Count" in item:
                device_sscount = item.split(" ")
                device_sscount = device_sscount[-1]
                #print "Start_stop_Count", device_sscount

            #THE FOLLOWING ARE KEY INDICATORS OF FAILURE (or recorded cause it can be)
            #https://www.backblaze.com/blog/hard-drive-smart-stats/

            #SMART 5 - Reallocated sector count
            if "5 Reallocate" in item:
                device_5reallocate = item.split(" ")
                device_5reallocate = device_5reallocate[-1]
                #print "Reallocated", device_5reallocate

            #SMART 187 Reported Uncorrectable Errors
            if item.startswith("187 Reported"):
                device_187ReportedUncorrectableErrors = item.split(" ")
                device_187ReportedUncorrectableErrors = device_187ReportedUncorrectableErrors[-1]
                #print "Reported Uncorrectable errors (187):", device_187ReportedUncorrectableErrors

            #SMART 188 Command Timeout
            if item.startswith("188 Command"):
                device_188CommandTimeout = item.split(" ")
                device_188CommandTimeout = device_188CommandTimeout[-1]
                #print "Command Timeout (188):", device_188CommandTimeout

            #SMART 197 Current Pending Sector Count
            if item.startswith("197 Current_Pending_Sector"):
                device_197CurrentPendingSector = item.split(" ")
                device_197CurrentPendingSector = device_197CurrentPendingSector[-1]
                #print "Current Pending Sector (197):", device_197CurrentPendingSector



            if "Temperature_Celsius" in item:
                device_tempC = item.split("(")
                device_tempC = device_tempC[0]
                device_tempC = device_tempC.split(" ")
                device_tempC = device_tempC[-2]
                #print "Temperature_Celsius", device_tempC

            if "198 Offline_Uncorrectable" in item:
                device_198OfflineUncorrectable = item.split(" ")
                device_198OfflineUncorrectable = device_198OfflineUncorrectable[-1]
                #print "Offline_Uncorrectable (198)", device_198OfflineUncorrectable

            # Need to think about device statistics - ie GP04.
            # - Device bytes written (logical blocks written/read to TB)
            # - Device io commands completed,  Lifetime, per hr average.
        append_data = slashdevid[0],device_model, device_serial, device_health, device_firmware_version, device_capacity, device_hrs, device_tempC, device_sscount, device_5reallocate, device_187ReportedUncorrectableErrors,device_188CommandTimeout,device_198OfflineUncorrectable,
        smart_device_info.append(append_data)

    return smart_device_info




def fnExportToCSV(smart_device_table,filename):
    #export pool data
    with open (filename, 'w') as csvfile:
        writeout = csv.writer(csvfile, quoting=csv.QUOTE_NONE)
        for line in smart_device_table:
            writeout.writerow(line)


#Run the bits we need:
smart_device_table = fnGetSmartData()
fnExportToCSV(smart_device_table,"/root/temp/monitoring/smartsatadata.txt")
