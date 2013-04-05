#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# This nagiosplugin was written to catch filesystems being remounted as readonly.
#
# Copyright (C) 2012 Morten Bekkelund
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# See: http://www.gnu.org/copyleft/gpl.html
#

import re
import sys

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

if __name__ == "__main__":
    ''' 
        check the status of the filesystems and provide nagios-output 
    '''

    status = return_ro_mounts()
    if status:
        print "CRITICAL: {0} mounted READ-ONLY.".format(status)
        sys.exit(1)
    else:
        print "OK: All disks mounted READ-WRITE."
        sys.exit(0)
