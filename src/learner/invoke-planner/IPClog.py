#!/usr/bin/python
#
# IPClog.py
# Description: Simple class which redirects the output to a given log
#              file according to a very simple format
# -----------------------------------------------------------------------------
#
# Started on  <Mon Mar 21 12:52:38 2011 Carlos Linares Lopez>
# Last update <Friday, 11 November 2011 23:03:51 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPClog.py 306 2011-11-11 22:25:37Z clinares                          $
# $Date:: 2011-11-11 23:25:37 +0100 (Fri, 11 Nov 2011)                       $
# $Revision:: 306                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@korf.plg.inf.uc3m.es>
#

# -----------------------------------------------------------------------------
#     This file is part of IPCData
#
#     IPCData is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     IPCData is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with IPCData.  If not, see <http://www.gnu.org/licenses/>.
#
#     Copyright Carlos Linares Lopez, 2011
# -----------------------------------------------------------------------------

"""
Simple class which redirects the output to a given log file according to a very simple format
"""

__version__  = '1.2'
__revision__ = '$Revision: 306 $'

import datetime         # date/time

# -----------------------------------------------------------------------------
# IPClog
#
# simple class which redirects the output to a given log file
# according to a very simple format
# -----------------------------------------------------------------------------
class IPClog(object):
    """
    simple class which redirects the output to a given log file
    according to a very simple format
    """

    # constructor
    def __init__ (self, logfile):
        """
        the constructor attachs an output stream to this log
        """

        try:
            self._file = open (logfile, 'w')
        except:
            print """
 Fatal Error - It was not possible to open/create the logfile '%s'""" % logfile
            raise IOError

        self.open ()
        
    # show the header
    def open (self):
        """
        show the header
        """
        self._file.write ('\n [' + \
                          datetime.datetime.now ().strftime ("%a, %m-%d-%y %H:%M:%S.%f") + ']')


    # show the footer
    def close (self):
        """
        show the footer
        """
        self._file.write (' [' + \
                          datetime.datetime.now ().strftime ("%a, %m-%d-%y %H:%M:%S.%f") + ']\n\n')
        self._file.close ()


    # alias hiding the inner writting service
    def write (self, string):
        self._file.write (string)


    # the next two services enable this class to be used in with statements
    
    # write the header
    def __enter__(self):
        """
        write the header
        """
        self.open ()


    # write the footer
    def __exit__(self, type, value, traceback):
        """
        write the footer
        """ 
        self.close ()


# Local Variables:
# mode:python
# fill-column:80
# End:
