#!/usr/bin/env python
#
# The intention of this script is to replace NRPE, ssh etc for remote execution
# of nagiosplugins. The script runs as root on the salt-master.
#

import sys
import argparse
import salt.client

# exitcodes for nagios .. pretty much just using unknown for now, but still :P
NAGIOS_EXIT = {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}

client = salt.client.LocalClient()

def execute_plugin(host,plugin,timeout):
	""" 
		executing nagiosplugin via salt's cmd.run_all function
	"""

	ret 	= client.cmd(host, "cmd.run_all", [plugin], timeout=timeout)
	exit 	= ret[host]["retcode"]
	output 	= ret[host]["stdout"]

	return exit, output

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Options:')
	parser.add_argument('-H', metavar='host', type=str, help='remote host to be queried', required=True)
	parser.add_argument('-p', metavar='plugin', type=str, help='full path to remote nagiosplugin', required=True)
	parser.add_argument('-t', metavar='timeout', type=str, help='timout in seconds', required=False)

	try:
		arguments = parser.parse_args()
	except Exception as e:
		print "Error in argumentparsing: {0}".format(e)
		sys.exit(NAGIOS_EXIT["UNKNOWN"])

	(exit, output) = execute_plugin(arguments.H,arguments.p,arguments.t)
	if not output:
		print "Remote execution of {0} unsuccessful.".format(arguments.p)
		print "Check if the plugin exists on the remote host and that the permissions" \
				"are correct."

print(output)
sys.exit(exit)