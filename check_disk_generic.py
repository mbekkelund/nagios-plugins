#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#  
#  Copyright (C) 2012 Morten Bekkelund
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#  
#  See: http://www.gnu.org/copyleft/gpl.html
#
#
#  This plugin is checking every filesystem in fstab.
#  It checks if the filesystem is mounted and returns a warning if its not.
#  The plugin takes -w warning and -c critical params for disk usage.
#  You can skip filesystems in the skip = [] python list, or add them 
#  on the commandline using the -s param.
#  The plugin's -w and -c params can be overridden by a 
#  .nagios_check_disk file on the mounted disk (if the file exits).
#  format of the file is : 
#  /mountpoint|warning|critical
#  ex:
#  /tmp|30|20
#  The reason for this is to let owners of the mounted disks decide the 
#  thresholds. (Less work for the sysadmin and more "shoot yourself in the foot"
#  for the owners.

import os
import argparse
import re
import socket

skip = ['/proc','none']
status = 0 # for picking up exitstatus
configfile = ".nagios_check_disk"
fstabfile = "/etc/fstab"
debug = 0
exit_status = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3}

def return_ro_mounts():
    ''' 
        open /proc/mounts and return local mounted readonly filsystems 
        (skipping non-real and remote filesystems)
    '''

    # a list of all filesystems we want to check 
    truefs = ['ext','ext2','ext3','ext4','xfs','reiserfs']

    try:
        proc = open("/proc/mounts","r")
    except:
        print "Failed to open file /proc/mounts."

    for line in proc.readlines():
            line = line.strip().split(" ")
            mp      = line[1]        # mountpoint
            fs      = line[2]        # filesystem
            status  = line[3][:2]    # ro/rw status
            ro_mounts = []
            if fs in truefs:
                if re.match("^ro",status):
                    ro_mounts.append(mp)
                    return ro_mounts

def read_config(dir,file):
    ''' in some cases we want to overwrite the generic checks params,
        so we'll read a configfile for this purpose...
        if its not there, default values will be used
    '''
    conf = []
    file = os.path.join(dir,file)
    if debug:
        print "reading {0}".format(file)
    try:
        f = open(file,"r")
        for l in f.readlines():
            if not l.startswith("#"):
                conf.append(l.rstrip())
    
        return conf
 
    except:
        ''' No configfile found, continuing with default values. '''

        return conf
        
def read_fstab():
    ''' reading fstab :P '''
    try:
        f = open(fstabfile,"r")
    except:
        print "Can not read fstab."
        exit(exit_status['UNKNOWN'])
        
    mounts = []
    for l in f.readlines():
        if not l.strip():
            continue 
        else:
            if not l.startswith('#'):
                mount = l.split()[1]
                fs    = l.split()[2]
                if arguments.s is None:
                    if not mount in skip:
                        mounts.append(mount) 
                else:
                    if not mount in skip and not fs in arguments.s:
                        mounts.append(mount) 
        
    return mounts

def get_fs_freespace(path):
    ''' return free space '''
    try:
        stat = os.statvfs(path)
        return stat.f_frsize*stat.f_bavail/1024/1024 #return in MB
    except:
        return "Could not read directory or mountpoint: {0}".format(path)

    
def get_fs_size(path):
    ''' return total space '''
    stat = os.statvfs(path)
    return stat.f_frsize*stat.f_blocks/1024/1024 #return in MB

def get_hostname():
    ''' return the hostname '''
    return socket.gethostname()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Options:')
    parser.add_argument('-w', metavar='warning', type=int, help='warning value in % (integer)', required=True)
    parser.add_argument('-c', metavar='critical', type=int, help='critical value in % (integer)', required=True)
    parser.add_argument('-s', metavar='skipfs', type=str, help='skip filesystems (ex: nfs,nfs4)', required=False, default=None)
    parser.add_argument('-ro', metavar='read-only', type=str, help='check if filesystems are mounted read-only', required=False)

    try:
        arguments = parser.parse_args()
    except:
        print "UNKNOWN: Error in argumentparsing"
        exit(exit_status['UNKNOWN'])

    output = []

    # checking for readonly mounts
    status = return_ro_mounts()
    if status:
        output.append("{0} mounted READ-ONLY.".format(status))
        status = exit_status['WARNING']
    else:
        #output.append("OK: All disks mounted READ-WRITE.")
        status = exit_status['OK']

    # checking if volumes are mounted according to fstab and the amount of free space pr mount
    skipfs = []
    if arguments.s:
        skipfs = arguments.s.split(',')

    fstab = read_fstab()
    host = get_hostname()

    for mount in fstab:
        if os.path.ismount(mount):
            conf = read_config(mount,configfile)
            free = get_fs_freespace(mount) 
            size = get_fs_size(mount) 
            free_pct = int(round((100 * float(free)/float(size))))
            for ll in conf:
                path,warning,critical = ll.split("|")
                if mount == path:
                    if debug:
                        print "partition: {0} using custom values, warning: {1}%, critical: {2}% (actualsize: {3}MB actualfree: {4}MB = {5}%)".format(path,warning,critical,size,free,free_pct)
                    if free_pct < int(critical):
                        output.append("{0} CRITICAL ({1}% free)".format(path,free_pct))
                        status = exit_status['CRITICAL']
                    elif free_pct < int(warning):
                        output.append("{0} WARNING ({1}% free)".format(path,free_pct))
                        status = exit_status['WARNING']
                    break
            else:
                if free_pct < int(arguments.c):
                    output.append("{0} CRITICAL ({1}% free)".format(mount,free_pct))
                    status = exit_status['CRITICAL']
                elif free_pct < int(arguments.w):
                    output.append("{0} WARNING ({1}% free)".format(mount,free_pct))
                    status = exit_status['WARNING']
         
                if debug:
                    print "partition: {0} using default values. warning: {3}%, critical: {4}% (actualsize: {1}MB actualfree: {2}MB = {5}%)".format(mount,size,free,arguments.w,arguments.c,free_pct)
        else:
            output.append("WARNING: {0} not mounted, but exists in fstab.".format(mount))
            status = exit_status['WARNING'] # warning if disks are not mounted
    if not exit_status == 0:
        print "{0}".format(output,exit_status)
        exit(status)
    else: 
        print "All good!".format(output,exit_status)
        exit(status)
                
