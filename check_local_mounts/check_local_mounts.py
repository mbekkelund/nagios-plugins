#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
import sys

def return_ro_mounts():
    ''' open /proc/mounts and return local mounted readonly filsystems 
        (skipping non-real and remote filesystems)
    '''

    # a dictionary of all filesystems we want to check 
    truefs = ['ext','ext2','ext3','ext4','xfs','reiserfs']

    try:
        proc = open("/proc/mounts","r")
    except Exception as e:
        print "Failed to open file. {0}".format(e)

    for line in proc.readlines():
            line = line.strip()
            mp      = line.split(" ")[1]        # mountpoint
            fs      = line.split(" ")[2]        # filesystem
            status  = line.split(" ")[3][:2]    # ro/rw
            ro_mounts = []
            if fs in truefs:
                if re.match("^ro",status):
                    ro_mounts.append(mp)
                    return ro_mounts

if __name__ == "__main__":
    ''' check the status of the filesystems and provide nagios-output '''

    status = return_ro_mounts()
    if status:
        print "CRITICAL: {0} mounted READ-ONLY.".format(status)
        sys.exit(1)
    else:
        print "OK: All disks mounted READ-WRITE."
        sys.exit(0)
