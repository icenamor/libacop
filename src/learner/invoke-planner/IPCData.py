#!/usr/bin/python
#
# IPCData.py
# Description: This class contains information about the IPC 2011
# -----------------------------------------------------------------------------
#
# Started on  <Wed Jan 26 12:42:30 2011 Carlos Linares Lopez>
# Last update <Friday, 11 November 2011 23:04:00 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPCData.py 306 2011-11-11 22:25:37Z clinares                         $
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
This class contains information about different assets of the IPC 2011
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.2'
__revision__ = '$Revision: 306 $'

# imports
# -----------------------------------------------------------------------------
import os                               # files and dirs mgmt

# -----------------------------------------------------------------------------
# IPCPlanner
#
#     This class implements information about a specific planner
# -----------------------------------------------------------------------------
class IPCPlanner:
    """
    This class implements information about a specific planner
    """

    # default constructor
    def __init__ (self, name, abbvtrack, abbvsubtrack, directory):
        """
        default constructor
        """

        # copy all the attributes
        self._name = name.lower ()
        self._abbvtrack = abbvtrack.lower ()
        self._abbvsubtrack = abbvsubtrack.lower ()

        # test the directory exists
        if (not os.path.exists (directory)):
            raise NameError, directory

        # test also that this directory holds a planner (which is
        # assumed to be the one specified) by looking for the
        # mandatory files build and plan
        if (not os.path.isfile (directory + '/build')):
            raise IndexError, 'build'
        if (not os.path.isfile (directory + '/plan')):
            raise IndexError, 'plan'

        if (directory [-1] == '/'):
            self._directory = directory
        else:
            self._directory = directory + '/'

        # and now process them
        self._track = { 'seq'   : 'sequential',  
                        'tempo' : 'temporal'} [self._abbvtrack]
        
        self._subtrack = { 'sat' : 'satisficing',  
                           'opt' : 'optimization',  
                           'mco' : 'multicore'} [self._abbvsubtrack]
        self._signature = self._abbvtrack + '-' + self._abbvsubtrack + \
                          '-' + self._name

        # set the default values
        self._questionnaire = "<None>"
        

    # printing service for user-friendly displays
    def __str__ (self):
        s  = " name      : %s\n" % self._name           # show attributes
        s += " track     : %s\n" % self._track    
        s += " subtrack  : %s\n" % self._subtrack 
        s += " signature : %s\n" % self._signature
        s += " directory : %s"   % self._directory
        
        return s                                        # return the string

    # read the pddlsupportquestionnaire from the directoy. It attempts
    # at reading the contents of a file 'questionnaire' If none is
    # found, an exception is raised
    def read_pddlsupportquestionnaire (self):
        """
        read the pddlsupportquestionnaire from the directoy. It
        attempts at reading the contents of a file 'questionnaire' If
        none is found, an exception is raised
        """

        # check the questionnaire does exist
        if (not os.path.isfile (self._directory + 'questionnaire.txt')):
            raise IndexError, 'questionnaire.txt'
        
        # read the questionnaire and write it to a dedicated attribute
        stream = open (self._directory + 'questionnaire.txt', 'r')
        self._questionnaire = stream.read ()

    # show the questionnaire
    def write_pddlsupportquestionnaire (self):
        """
        show the pddl support questionnaire
        """

        print self._questionnaire

        
        

# Local Variables:
# mode:python
# fill-column:80
# End:
