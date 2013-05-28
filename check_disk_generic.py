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

import os
import argparse
import re
import socket

skip = ['/proc','none']
exit_status = 0 # unknown, we dont know what the status is yet
configfile = ".nagios_check_disk"
fstabfile = "/etc/fstab"
debug = 0

def read_config(dir,file):
    ''' in some cases we want to overwrite the generic checks params,
        so we'll read a configfile for this purpose...
        if its not there, default values will be used
    '''
    conf = []
    if dir == "/":
        file=dir+file
    else:
        file=dir+'/'+file
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
        exit(3)
        
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
    ''' return free space '''
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
    try:
        arguments = parser.parse_args()
    except:
        print "UNKNOWN: Error in argumentparsing"
        exit(3)

    skipfs = []
    if arguments.s:
        skipfs = arguments.s.split(',')

    fstab = read_fstab()
    host = get_hostname()
    output = []
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
                        exit_status = 2
                    elif free_pct < int(warning):
                        output.append("{0} WARNING ({1}% free)".format(path,free_pct))
                        exit_status = 1
                    break
            else:
                if free_pct < int(arguments.c):
                    output.append("{0} CRITICAL ({1}% free)".format(mount,free_pct))
                    exit_status = 2
                elif free_pct < int(arguments.w):
                    output.append("{0} WARNING ({1}% free)".format(mount,free_pct))
                    exit_status = 1
         
                if debug:
                    print "partition: {0} using default values. warning: {3}%, critical: {4}% (actualsize: {1}MB actualfree: {2}MB = {5}%)".format(mount,size,free,arguments.w,arguments.c,free_pct)
        else:
            output.append("WARNING: {0} not mounted, but exists in fstab.".format(mount))
            exit_status = 1 # warning if disks are not mounted
    if not exit_status == 0:
        print "{0}".format(output,exit_status)
        exit(exit_status)
    else: 
        print "All good!".format(output,exit_status)
        exit(exit_status)
                
