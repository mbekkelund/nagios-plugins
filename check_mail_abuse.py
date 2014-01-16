#!/usr/bin/env python
#
# This plugin was written to discover suspicious activity coming from 
# our companys mailboxes. Suddenly one guy had sent close to 40k mails
# in a week and we started getting blocked here and there on da interwebs :)
#
# 2013 - Morten Bekkelund bekkelund@gmail.com
##############################################################################
# 15. Disclaimer of Warranty.
#
# THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
# APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
# HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
# OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
# IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
# ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
#
# 16. Limitation of Liability.
#
# IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
# WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
# THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
# GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
# USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
# DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
# PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
# EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGES.
##############################################################################
#
#

import re
import datetime
import argparse
import sys

NAGIOS_EXIT = {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": 3}
skip_users = ['root','www','nagios','pgsql','noreply'] # stuff we might not be interested in having in our output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Options:')
    #parser.add_argument('-s', metavar='suspicious', type=int, help='set amount of mails sent before reporting suspicious activity', required=False, default=555)
    parser.add_argument('-m', metavar='multiply', type=bool, help='set to true if the suspicious value should be multiplied by weekday (since the log grows pr day)', required=False, default=True)
    parser.add_argument('-l', metavar='logfile', type=str, help='full path of the mail.log logfile (default=/var/log/mail.log)', required=False, default="/var/log/mail.log")
    parser.add_argument('-d', metavar='debug', type=bool, help='turn debugging on/off', required=False, default=False)
    parser.add_argument('-u', metavar='skipusers', type=str, help='commaseparated list of users not to include in the output', required=False)
    parser.add_argument('-w', metavar='warning', type=int, help='report a warning if suspicious param is higher than this', required=True)

    try:
        arguments = parser.parse_args()
    except Exception as e:
        print "Error in argumentparsing: {0}".format(e)
        sys.exit(NAGIOS_EXIT["UNKNOWN"])

    # since logrotation happens on sunday morning, we'll multiply the suspicious-value by weekday
    # this mismatches a little on sundays (sundays being day 6 in python and logrotation might
    # be happening in the mornings :P ..adjust it or fix the script)
    if arguments.m:
        if datetime.datetime.today().weekday() > 0:
            arguments.w = arguments.w * datetime.datetime.today().weekday() 

    if arguments.u:
        for u in arguments.u.split(","):
            skip_users.append(u)

    senders = dict()
    maillog = open(arguments.l, 'r').readlines()

    for line in maillog:
        
        if re.search("(?<=from=<)\w+", line):
            m = re.search('\w+@[\w.-]+', line)
            if m:
                sender = m.group(0)
                user   = sender.split("@")[0] # need this for skip_users matching

                if not user in skip_users: 
                    if senders.get(sender):
                        senders[sender] = senders.get(sender) + 1
                    else:
                        senders[sender] = 1

    if arguments.d:
        print "=== Settings: ==="
        print "Using logfile: {0}".format(arguments.l)
        print "Warning is currently set to {0} mails sent.".format(arguments.w)
        print "Skipping users: {0}".format(skip_users)
        print "=== Users and values: ==="

    output = list()
    for s in sorted(senders, key=senders.get, reverse=False):
        if senders[s] > arguments.w:
            output.append("{0}: {1}".format(s,senders[s]))

    if output:
        print "WARNING: suspicious amount? {0}".format(output)
        sys.exit(NAGIOS_EXIT["WARNING"])

    print "OK. Everything seems fine."
    sys.exit(NAGIOS_EXIT["OK"])
