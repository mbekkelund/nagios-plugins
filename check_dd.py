#!/usr/bin/env python
# -*- coding: UTF-8 -*-

##############################################################################
#   Nagios-plugin that runs a dd-command to measure write-speed to a mountpoint.
#   2012 - mortenb@met.no
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
import argparse, subprocess, re, os


class file_obj:
	def __init__(self):
		self.speed = False
		self.units = False
		self.tmpfile = "/tmp/nagios_dd_tmpfile"
  		self.ddfile = ".nagios-dd-test"
		self.filecontent = False

	def run_dd(self, directory, count):
		""" dd a file into a directory and return writespeed. """
		os.system("dd if=/dev/full of="+directory+"/"+self.ddfile+" bs=1M count="+str(count)+" > "+self.tmpfile+" 2>&1 &")

	def check_space(self,directory):
		""" check if there is sufficent space on the disk to run dd with requested filesize """
		disk = os.statvfs(directory)
		available = (disk.f_frsize * disk.f_bavail) / 1024 
		return available
	
	def read_file(self):
		""" reads the buffered dd file from previous run """
		if os.path.exists(self.tmpfile):
			f = open(self.tmpfile)
			output = f.read().split("\n")[2].split(",")[2]
			self.speed = int(re.search('(\d+)', output).group(0).strip(' \t\n\r'))
			self.units = re.search('([A-Z].*)', output).group(0).strip(' \t\n\r')
			f.close()
			# running new dd
			file_obj().run_dd(arguments.d,arguments.s)
			return self
		else:
			print "UNKNOWN: tmpfile does not exist. Wait for next run."
			# running new dd
			file_obj().run_dd(arguments.d,arguments.s)
			exit(3)
			
		
		

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Options:')
	parser.add_argument('-d', metavar='directory', type=str, help='the directory where the dd-file is to be written', required=True)
	parser.add_argument('-w', metavar='warning', type=int, help='warning value in MB/s (integer)', required=True)
	parser.add_argument('-c', metavar='critical', type=int, help='critical value in MB/s (integer)', required=True)
	parser.add_argument('-s', metavar='size', type=int, help='size of dd-file to be written in MB', required=True)

	try:
		arguments = parser.parse_args()
	except:
		print "UNKNOWN: Error in argumentparsing"
		exit(3)

	# performing a check on the volume to see if it has enough space for the dd-file to be written 
	space = file_obj().check_space(arguments.d)
	if space < (arguments.s * 1024):
		print "UNKNOWN: Cannot perform dd on the volume. Not enough space."
		exit(3)

	# reading tmpfile from previous run
	result = file_obj().read_file()


	speed = result.speed
	units = result.units
		

	# if its GB/s we dont even care!
	if units == "GB/s":
  		print "OK: According to YOU %s %s is all good!" % (speed, units)
      		exit(0)
 	# but if its MB/s ...we should check the speed
	elif units == "MB/s":
   		if arguments.c > speed:
			print "CRITICAL: OMG %s %s is less than %s" % (speed, units, arguments.c)
			exit(2)
		elif arguments.w > speed: 
			print "WARNING:  OMG %s %s is less than %s" % (speed, units, arguments.w)
			exit(1)
		else:
			print "OK: According to YOU %s %s is all good!" % (speed, units)
			exit(0)
	# and if it aint the two above, we're pretty much screwed
	else:
		print "CRITICAL: OMG %s %s is like ....FAIL" % (speed, units)
		exit(2)

