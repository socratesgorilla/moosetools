#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

#this hack is copied from https://gist.github.com/CMCDragonkai/fe342b958e013078d72500d286973075
#i don't understand the code, but nothing works without


import sys, os.path as path
from inspect import getsourcefile

parent_dir = path.dirname(path.dirname(path.abspath(getsourcefile(lambda: 0))))
sys.path.append(path.join(parent_dir, 'moosetools'))

# make sure to hack the sys.path
# before importing your own modules

from . import *
#from .mms import *