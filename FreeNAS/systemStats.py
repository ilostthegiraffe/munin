#!/usr/bin/env python

#
# Script to get ZFS system config.  Dump all to lists, and ultimately to csv.
#


#import handy commands
import os
import sys
import re
import time
import datetime
import csv

#Configure Arrays to store data
pools=['TANK', "SSD"]
pool_info=[]
pool_compressratio=[]
smart_devices=[]
smart_device_info=[]
CC_dev_list = []
current_unix_time = int(time.time())

#zpool info
def fnZFSpoolstats(pools):
	pool_devices=[]
	pool_compressratio_headers = ["Unix Timestamp","Pool Name", "Description", "CompressRatio", "-"]
	pool_compressratio.append(pool_compressratio_headers)
	pool_info_headers = ["Unix Timestamp","Pool Name", "Size", "Used", "Used %", "Fragmentation %", "Pool ID", "Scan Info",  "Errors"]
	pool_info.append(pool_info_headers)
	pool_devicesheader = ["Unix Timestamp","Pool Name", "vDev Type", "Member gptid", "Member Status"]
	pool_devices.append(pool_devicesheader)

	for index, pool in enumerate(pools):
		#ZFS list import
		pool_info_raw = os.popen("/sbin/zpool list -H -o name,size,alloc,cap,frag,health,guid " + pool).read().strip().split()
		pool_info_raw.insert(0,current_unix_time)
		pool_info_raw = pool_info_raw
		#print "POOL INFO RAW", pool_info_raw
		'''pool compression'''

		pool_compress_raw=os.popen("zfs get compressratio " + pool + " | grep compress").read().strip().split()
		pool_compress_raw.insert(0, current_unix_time)
		pool_compressratio.append(pool_compress_raw)

		'''zfs status import'''
		zfs_status_raw = os.popen("zpool status " + pool).read().strip().split('\n')
		zfs_status_raw_linebyline=[]
		for item in zfs_status_raw:
			item = item.split('  ')
			zfs_status_raw_linebyline.append(item)

		'''add pool error message'''
		#print "POOLINFO...", pool_info
		for line in zfs_status_raw_linebyline:
			#print "line>", line
			if "errors:" in line[0]:

			#	print "Adding to pool_info",index,",line",line[0]

				pool_info_raw.append(line[0])
				#print"POOL INFO RAW PLUS ERROR", pool_info_raw

			'''add pool scan information'''

			if len(line) > 1:
				#print "LINE OF LEN2", line
				if "scan:" in line[1]:
					scandata =",".join(line[1:])
					scandata= scandata.replace(",","")
					pool_info_raw.append(scandata)

		if "scan:" not in pool_info_raw[-2]:
			print "broken"

		pool_info.append(pool_info_raw)

		'''Parse ZFS status for vdevs and members'''
		#find mirror or raid"
		eof = len(zfs_status_raw_linebyline)
		vdev_line_location=[]
		for index, line in enumerate(zfs_status_raw_linebyline):
			if len(line) > 2:

				if "raid" in line[1]:
					vdev_line_location.append(index)

				if "mirror" in line[1]:
					vdev_line_location.append(index)


		#we know where the vdevs start and finish, so we can write to the array
		listlength = len(vdev_line_location)
		listlength = listlength -1

		for index, location in enumerate(vdev_line_location):

			if index < listlength:
				end_of_run = vdev_line_location[index+1]
			else:
				end_of_run = eof

			for item in range(location,end_of_run)[1:]:
					if len(zfs_status_raw_linebyline[item])==11:
						append_data=pool,zfs_status_raw_linebyline[location][1],zfs_status_raw_linebyline[item][2], \
						zfs_status_raw_linebyline[item][3]

						pool_devices.append(append_data)


	return pool_devices

def fnGpt_labels():
	gpt_labels=[]
	'''Get gptid names and their components    gpt_labels'''
	gpt_list_raw=os.popen("glabel status | grep gptid").read().split('\n')

	gpt_labels_headers = "gptid","DA Address"
	gpt_labels.append(gpt_labels_headers)

	for device in gpt_list_raw[0:-1]:
		device=device.split()
		dev_label=device[0],device[2]

		gpt_labels.append(dev_label)
	return gpt_labels

def fnCamcontroDevlist():
	#get list of devices in system
	smart_list_devices_raw=os.popen("camcontrol devlist").read().split('\n')

	#headers for list
	CC_dev_list_headers = "Unix Timestamp", "Full Device Name", "Address"
	CC_dev_list.append(CC_dev_list_headers)

	for line in smart_list_devices_raw[:-2]:
		name=line.split('>')
		name = name[0][1:]


		addr = line.split(",")
		addr = addr[0].split("(")
		addr = addr[-1]
		appendthis = current_unix_time, name, addr
		CC_dev_list.append(appendthis)
	return CC_dev_list

def fnImportSASSMART(smart_devices):

	'''Import SAS SMART DATA'''

	#just to keep it quiet in testing

	smart_devices = ['4','5']
	#Write out first line arry headers
	smart_headers = "Unix Timestamp", "DA", "Product", "Serial", "Firmware", "SMART", "Size", "Hrs", "StartStop", "EGD", "Temp", \
	"GB_Read", "EEC_R", "UncorrectR", "GB_Write", "EEC_W", "UncorrectW","NonMedium","Date Manufactured"
	smart_device_info.append(smart_headers)

	for slashdevid in smart_devices:
		#not all drives support all varibles, if script breaks, add in the trouble makers here with a debug value.
		device_model = "-10"
		device_serial = "-20"
		device_health = "-30"
		device_firmware_version = "-40"
		device_capacity = "-50"
		device_hrs = "-60"
		device_tempC = "-70"
		device_sscount = "-80"
		device_growndefect = "-90"

		slashid=slashdevid[0]
		#add in slashid rather tahn ada1 to make this work!
		#smart_device_data=os.popen("smartctl -a " + slashdevid[0] ).read().split('\n')
		smart_device_data = open("sas-x.txt").readlines()

		#print "sdd:", smart_device_data
		#print "raw", smart_device_data
		#print "rawline:", smart_device_name



		#scan through smart_device_data for data to grab
		for index, item in enumerate(smart_device_data):
			item = item.replace("\n", "")
			#print 'raw item', item
			if "Product:" in item:
				device_model = item.split(':')[-1]
				device_model = device_model.split(" ")[-1]
				#print "device_model", device_model

			if "Revision:" in item:
				device_firmware_version = item.split(':')[-1]
				device_firmware_version = device_firmware_version.split(' ')[-1]
				#print "device firmware:", device_firmware_version

			if "Serial number:" in item:
				device_serial = item.split(':')[-1]
				device_serial = device_serial.split(' ')[-1]
				#print "device serial:", device_serial

			if "SMART Health Status" in item:
				device_health = item.split (":")[-1][1:]
				#print "Smart health", device_health

			if "User Capacity" in item:
				device_capacity = item.split("[")
				device_capacity =  device_capacity[1].replace("]", "")
				#print "device_capacity", device_capacity

			if "Accumulated power on time" in item:
				device_hrs = item.split(":")[1]
				device_hrs = device_hrs.split(" ")[-1]
				#print "Power on hrs", device_hrs

			if "Accumulated start-stop cycles:" in item:
				device_sscount = item.split(":")[1]
				device_sscount = device_sscount.split(" ")[-1]
				#print "Start_stop_Count", device_sscount

			if "Manufactured in week " in item:
				date = item.split()[3] + "/" + item.split()[6]
				device_dateManufactured = int(time.mktime(datetime.datetime.strptime(date, "%W/%Y").timetuple()))
				#print "date Manufactured", date



			#THE FOLLOWING ARE KEY INDICATORS OF FAILURE (or recorded cause it can be)
			#https://www.backblaze.com/blog/hard-drive-smart-stats/

			#SMART 5 - Reallocated sector count
			if "Elements in grown defect" in item:
				device_growndefect = item.split(":")[-1]
				device_growndefect = device_growndefect.split()[-1]
				#print "Grown defect", device_growndefect

			#Current Drive Temp
			if item.startswith("Current Drive Temperature"):
				device_tempC = item.split(":")[1]
				device_tempC = device_tempC.split()[-2]
				#print "Temperature_Celsius", device_tempC


			#======================
			# Drive Read/writes & Errors
			#======================

			# Read statistics
			if item.startswith("read: "):
				#GB Read
				device_GBRead = item.split()[-2]
				#print "GB Read:", device_GBRead
				#ECC Errors Corrected Read
				device_ECCRead = item.split()[4]
				#print "GB ECC Read:", device_ECCRead
				#Uncorrected Errors (187)
				device_UncorrectableErrorsRead = item.split()[-1]
				#print "Uncorrectable Errors Read", device_UncorrectableErrorsRead


			#Write statistics
			if item.startswith("write: "):
				#GB Write
				device_GBWrite = item.split()[-2]
				#print "GB Write:", device_GBWrite
				#EEC Errors Corrected Write
				device_EECWrite = item.split()[4]
				#print "Write ECC Errors:", device_EECWrite
				device_UncorrectableErrorsWrite = item.split()[-1]
				#print "Uncorrectable ErrorsWrite:", device_UncorrectableErrorsWrite


			#Non Medium Errors
			if item.startswith("Non-medium error count:"):
				device_NonMediumErrorCnt = item.split(":")[1]
				device_NonMediumErrorCnt = device_NonMediumErrorCnt.split()[-1]
				#print "Non Medium Error Count", device_NonMediumErrorCnt



		#Append the device stats to the array.
		append_data =current_unix_time, slashdevid[0],device_model, device_serial, device_firmware_version, device_health, \
		device_capacity, device_hrs, device_sscount, device_growndefect, device_tempC, device_GBRead, device_ECCRead, \
		device_UncorrectableErrorsRead,device_GBWrite, device_EECWrite, device_UncorrectableErrorsWrite,device_NonMediumErrorCnt, \
		device_dateManufactured

		smart_device_info.append(append_data)
	return smart_device_info

def fnImportSATA():
	'''print"---------Import SATA SMART DATA------------------"

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
		print "slash0", slashdevid[0]
		slashid=slashdevid[0]
		#add in slashid rather tahn ada1 to make this work!
		smart_device_data=os.popen("smartctl -a " + slashdevid[0] ).read().split('\n')

		#print "raw", smart_device_data


		#print "rawline:", smart_device_name
		#scan through smart_device_data for name field
		for index, item in enumerate(smart_device_data):
			print 'raw item', item
			if "Device Model" in item:
				device_model = item[18:]
				print "device_model", device_model


			if "Firmware Version:" in item:
				device_firmware_version = item[17:]
				print "device firmware:", device_firmware_version


			if "Serial" in item:
				device_serial = item[17:]
				print "device serial:", device_serial


			if "SMART overall-health self-assessment" in item:
				device_health = item.split (":")
				device_health = device_health[1]
				print "Smart health", device_health


			if "User Capacity" in item:
				device_capacity = item.split("[")
				device_capacity =  device_capacity[1].replace("]", "")
				print "device_capacity", device_capacity


			if "Power_On_Hours" in item:
				device_hrs = item.split(" ")
				device_hrs = device_hrs[43:][0]
				print "Power on hrs", device_hrs


			if "4 Start_Stop_Count" in item:
				device_sscount = item.split(" ")
				device_sscount = device_sscount[-1]
				print "Start_stop_Count", device_sscount

			#THE FOLLOWING ARE KEY INDICATORS OF FAILURE (or recorded cause it can be)
			#https://www.backblaze.com/blog/hard-drive-smart-stats/

			#SMART 5 - Reallocated sector count
			if "5 Reallocate" in item:
				device_5reallocate = item.split(" ")
				device_5reallocate = device_5reallocate[-1]
				print "Reallocated", device_5reallocate

			#SMART 187 Reported Uncorrectable Errors
			if item.startswith("187 Reported"):
				device_187ReportedUncorrectableErrors = item.split(" ")
				device_187ReportedUncorrectableErrors = device_187ReportedUncorrectableErrors[-1]
				print "Reported Uncorrectable errors (187):", device_187ReportedUncorrectableErrors

			#SMART 188 Command Timeout
			if item.startswith("188 Command"):
				device_188CommandTimeout = item.split(" ")
				device_188CommandTimeout = device_188CommandTimeout[-1]
				print "Command Timeout (188):", device_188CommandTimeout

			#SMART 197 Current Pending Sector Count
			if item.startswith("197 Current_Pending_Sector"):
				device_197CurrentPendingSector = item.split(" ")
				device_197CurrentPendingSector = device_197CurrentPendingSector[-1]
				print "Current Pending Sector (197):", device_197CurrentPendingSector



			if "Temperature_Celsius" in item:
				device_tempC = item.split("(")
				device_tempC = device_tempC[0]
				device_tempC = device_tempC.split(" ")
				device_tempC = device_tempC[-2]
				print "Temperature_Celsius", device_tempC

			if "198 Offline_Uncorrectable" in item:
				device_198OfflineUncorrectable = item.split(" ")
				device_198OfflineUncorrectable = device_198OfflineUncorrectable[-1]
				print "Offline_Uncorrectable (198)", device_198OfflineUncorrectable

			# Need to think about device statistics - ie GP04.
			# - Device bytes written (logical blocks written/read to TB)
			# - Device io commands completed,  Lifetime, per hr average.
		append_data = slashdevid[0],device_model, device_serial, device_health, device_firmware_version, device_capacity, device_hrs, device_tempC, device_sscount, device_5reallocate, device_187ReportedUncorrectableErrors,device_188CommandTimeout,device_198OfflineUncorrectable,
		smart_device_info.append(append_data)'''

def prepForExportToCsv():

	print "ready!"


def fnExportToCSV(exportDataList,filename):
	#export pool data
	with open (filename, 'a') as csvfile:
		writeout = csv.writer(csvfile, quoting=csv.QUOTE_NONE)
		for line in exportDataList[1:]:
			writeout.writerow(line)

			print line

	print "Exported"


#build data for export
pool_devices = fnZFSpoolstats(pools)
gpt_labels = fnGpt_labels()
smart_devices  = fnImportSASSMART(gpt_labels)
CC_dev_list = fnCamcontroDevlist()
#fnExportToCSV(smart_device_info,"smart.txt")
#fnExportToCSV(pool_devices,"pool.txt")


print "===============Pool_devices detected Summary==============="
for item in pool_devices:
	print item

print"===============Pool info Summary==========================="
for item in pool_info:
	print item

print"===============Pool compression ratio==========================="
for item in pool_compressratio:
	print item

print"===============GPT label Summary==========================="
for item in gpt_labels:
	print item

print"===============RAW Devices Detected==========================="
for item in CC_dev_list:
	print item

print"===============SMART Data================="
for item in smart_device_info:
	print item
