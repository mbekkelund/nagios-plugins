#!/usr/bin/env python
# -*- coding: UTF-8 -*-

##############################################################################
#   Nagios-plugin that runs a dd-command to measure write-speed to a mountpoint.
#   2012 - morten bekkelund
##############################################################################
#   15. Disclaimer of Warranty.
#
#   THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
# APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
# HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
# OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
# IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
# ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
#
#   16. Limitation of Liability.
#
#   IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
# WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
# THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
# GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
# USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
# DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
# PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
# EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGES.
##############################################################################

# subprocess lets you run commands, argparse parses arguments from the commandline
import argparse
import subprocess
import re
import os

ERROR_CODES = {'OK':0, 'WARNING':1, 'CRITICAL':2, 'UNKNOWN':3}

speed = False
units = False
tmpfile = "/tmp/nagios_dd_tmpfile"
ddfile = ".nagios-dd-test"
filecontent = False

def run_dd(directory, count):
    """ dd a file into a directory and return writespeed. """
    os.system("dd if=/dev/full of={0}/{1} bs=1M count={2} > {3} 2>&1 &".format(directory,ddfile,str(count),tmpfile))

def check_space(directory):
    """ check if there is sufficent space on the disk to run dd with requested filesize """
    disk = os.statvfs(directory)
    available = (disk.f_frsize * disk.f_bavail) / 1024
    return available

def read_file():
    """ reads the buffered dd file from previous run """
    if os.path.exists(tmpfile):
        try:
            f = open(tmpfile)
            output = f.read().split("\n")[2].split(" ")[-2:]
            f.close()
            # running new dd
            run_dd(arguments.d,arguments.s)
            return output
        except IndexError as e:
            print "Plugin failed reading {0} (dd/plugin allready running?): Error: {1}".format(ddfile,e)
            exit(ERROR_CODES['UNKNOWN'])
    else:
        print "tmpfile does not exist. Wait for next run."
        # running new dd
        run_dd(arguments.d,arguments.s)
        exit(ERROR_CODES['UNKNOWN'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Options:')
    parser.add_argument('-d', metavar='directory', type=str, help='the directory where the dd-file is to be written', required=True)
    parser.add_argument('-w', metavar='warning', type=int, help='warning value in MB/s (integer)', required=True)
    parser.add_argument('-c', metavar='critical', type=int, help='critical value in MB/s (integer)', required=True)
    parser.add_argument('-s', metavar='size', type=int, help='size of dd-file to be written in MB', required=True)

    try:
        arguments = parser.parse_args()
    except:
        print "Error in argumentparsing"
        exit(ERROR_CODES['UNKNOWN'])

    # performing a check on the volume to see if it has enough space for the dd-file to be written
    space = check_space(arguments.d)
    if space < (arguments.s * 1024):
        print "Cannot perform dd on the volume. Not enough space."
        exit(ERROR_CODES['UNKNOWN'])

    # reading tmpfile from previous run
    result = read_file()

    speed = result[0]
    units = result[1]

    # if its GB/s we dont even care!
    if units == "GB/s":
        print "OK: According to YOU {0}{1} is all good!".format(speed, units)
        exit(ERROR_CODES['OK'])
     # but if its MB/s ...we should check the speed
    elif units == "MB/s":
        if arguments.c > speed:
            print "{0}{1} is less than {2}".format(speed, units, arguments.c)
            exit(ERROR_CODES['CRITICAL'])
        elif arguments.w > speed:
            print "{0}{1} is less than {2}".format(speed, units, arguments.w)
            exit(ERROR_CODES['WARNING'])
        else:
            print "According to YOU {0}{1} is all good!".format(speed, units)
            exit(ERROR_CODES['OK'])
    # and if it aint the two above, we're pretty much screwed
    else:
        print "{0}{1} is like ....FAIL".format(speed, units)
        exit(ERROR_CODES['CRITICAL'])

