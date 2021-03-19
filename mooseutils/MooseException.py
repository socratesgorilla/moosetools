#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html


class MooseException(Exception):
    """
    An Exception for MOOSE python applications that automatically applies the .format command.
    """
    def __init__(self, message, *args):
        Exception.__init__(self, message.format(*args))

    @property
    def message(self):
        return str(self)
