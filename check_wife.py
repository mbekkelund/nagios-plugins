#!/usr/bin/env python
"""

 See http://www.withings.com/en/api/bodyscale .

 The check_wife.py nagios-plugin was written by Morten Bekkelund
 Dont worry, the "wife" part is just a joke :)
 If you dont find it funny, rename it ;)
 You can find your userid/publickey on the withings.com pages
 log into your account, select "share" at the top
 select "share on my website" and you'll see your id/key
 BMI via nagios. Ofcourse ...you will need the withings bodyscale.

 Enjoy!

 Copyright (C) 2012 Morten Bekkelund

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 See: http://www.gnu.org/copyleft/gpl.html

 Original withingswrapper was fetched from : 
 https://github.com/mote/python-withings

"""

import urllib2
import simplejson
import sys
import argparse

# Settings
URL = 'http://wbsapi.withings.net/measure?action=getmeas&userid=%d&publickey=%s'

#globals
lastsize = 0
lastweight = 0
bmi = 0



class WithingsWrapper:
  TYPES = {
      1: 'weight',
      4: 'size',
      5: 'fat_free_mass',
      6: 'fat_ratio',
      8: 'fat_mass_weight',
      9: 'diastolic_blood_pressure',
      10: 'systolic_blood_pressure',
      11: 'pulse',
      }

  def _get_measurement_raw(self, id, key):
    """Get raw json for measurement."""
    url = URL % (id, key)
    content = urllib2.urlopen(url)
    json = simplejson.load(content)
    content.close()
    return json

  def get_measurements(self, id, key):
    """Yield (measure, value) tuple.
    """
    m = self._get_measurement_raw(id, key)
    m = m.get('body', {}).get('measuregrps', {})
    if not m:
      return

    count=0
    for entry in m:
      # Category 1 is actual measure, as opposed to objective.
      # Skip all others.
      if entry['category'] != 1:
        continue
      for measure in entry['measures']:
        count+=1
        if count <= 2:
            name = measure['type']
            name = self.TYPES.get(name, str(name))
            # actual value = value * 10^unit
            val = measure.get('value', 0) * (10 ** measure.get('unit', 0))
            if name == 'size':
                global lastsize
                lastsize = val
            if name == 'weight':
                global lastweight
                lastweight = val
                global bmi
                bmi = lastweight / (lastsize**2)
                break


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Options:')
    parser.add_argument('-u',metavar='userid',type=int, help='Your withings.com userid.',required=True)
    parser.add_argument('-k',metavar='apikey',type=str, help='Your witnings.com api-key.',required=True)
    parser.add_argument('-n',metavar='name',type=str, help='Name in output. Ex: \'wife\' or \'Morten\'',required=True)
    try:
        arguments = parser.parse_args()
    except:
        print "UNKNOWN: Error in argumentparsing."
        sys.exit(3)
        
    w = WithingsWrapper()
    data = WithingsWrapper.get_measurements(w,arguments.u,arguments.k)
    if bmi>25:
        print "WARNING: %s's overweight. Size: %s - Weight: %s BMI: %s"%(arguments.n,lastsize,lastweight,bmi)
        sys.exit(1)
    elif bmi<18.5:
        print "WARNING: %s's underweight. Size: %s - Weight: %s BMI: %s"%(arguments.n,lastsize,lastweight,bmi)
        sys.exit(1)
    else:
        print "OK: %s is all good! Size: %s - Weight: %s BMI: %s"%(arguments.n,lastsize,lastweight,bmi)
        sys.exit(0)

