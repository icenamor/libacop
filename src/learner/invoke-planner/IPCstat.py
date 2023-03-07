#!/usr/bin/python
#
# stats.py
# Description: definition of very basic stats gathered during the
#              running phase of the IPC
# -----------------------------------------------------------------------------
#
# Started on  <Mon Mar 21 12:14:08 2011 Carlos Linares Lopez>
# Last update <Saturday, 03 December 2011 22:58:48 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPCstat.py 308 2011-12-20 23:08:29Z clinares                         $
# $Date:: 2011-12-21 00:08:29 +0100 (Wed, 21 Dec 2011)                       $
# $Revision:: 308                                                            $
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
definition of very basic stats gathered during the running phase of the IPC
"""

__version__  = '1.2'
__revision__ = '$Revision: 308 $'

# imports
# -----------------------------------------------------------------------------
import PrettyTable                      # for creating pretty tables

# -----------------------------------------------------------------------------
# IPCsample
#
# this class attachs an observation to a tuple planner/domain
# -----------------------------------------------------------------------------
class IPCsample:

    """
    this class attachs an observation to a tuple planner/domain
    """

    # default constructor
    def __init__ (self, planner, domain, sample):

        # copy the values to the attributes of this instance
        self._planner = planner
        self._domain  = domain
        self._sample  = sample
    

# -----------------------------------------------------------------------------
# IPCstat
#
# this class simply updates a count of frequencies for a given
# collection of planner/domain
# -----------------------------------------------------------------------------
class IPCstat:

    """
    this class simply updates a count of frequencies for a given
    collection of planner/domain
    """

    # default constructor
    def __init__ (self, caption='', name='*'):

        # copy the stat attributes
        self._name = name
        self._caption = caption

        # create an empty histogram as a dictionary without keys
        self._histogram = {}


    # operator overloading
    def __repr__ (self):

        """
        show the stats stored at the given dictionary (which is
        assumed to store data as planner/domain) in both views showing
        also the subtotals
        """

        return self.prettytable ()


    def __iadd__ (self, other):

        if (other._planner not in self._histogram.keys ()):
            self._histogram [other._planner] = {}
            self._histogram [other._planner][other._domain] = other._sample

        else:
            if (other._domain not in self._histogram [other._planner].keys ()):
                self._histogram [other._planner][other._domain] = other._sample
            else:
                self._histogram [other._planner][other._domain] += other._sample

        return self


    # the following service encapsulates the access to the IPCsample
    # and eases the invocation of IPCstat
    def accumulate (self, planner, domain, sample):
        """
        the following service encapsulates the access to the IPCsample
        and eases the invocation of IPCstat
        """

        sample = IPCsample (planner, domain, sample)
        self += sample


    def prettytable (self):
        """
        creates a pretty table with the data stored in this dictionary
        """

        # compute the caption
        if self._caption:
            caption = " * " + self._caption + ":\n"

        # check there are planners ready to be printed
        if (len (self._histogram.keys ()) > 0):
            
            # First, get the name of all domains - the following statement does not
            # assume that all planners shall contain information of exactly the same
            # domains though this is necessarily true and, indeed, the remaining
            # code does assume it
            domains = sorted (list (set (reduce (lambda x,y : x+y,
                                                 [self._histogram [x].keys () for x in self._histogram.keys ()]))))

            # Now, create the the pretty table
            table = PrettyTable.PrettyTable ([self._name] + domains + ['total'])
            table.align [self._name] = 'l'
            for iplanner in sorted (self._histogram.keys ()):
                totalpln = reduce (lambda x,y:x+y,
                                   [self._histogram [iplanner][idomain] 
                                   for idomain in self._histogram [iplanner].keys ()])
                table.add_row ([iplanner] + 
                               [self._histogram [iplanner][idomain] 
                                for idomain in sorted (self._histogram [iplanner].keys ())] +
                               [totalpln])

            # and now compute the the totals by columns and print them out
            totaldmn = [reduce (lambda x,y:x+y,
                                [self._histogram [x][y] for x in self._histogram.keys ()])
                        for y in domains]
            table.add_row (['total'] + totaldmn + [''])
                

            # and show it along with the caption
            return caption + str (table)
        
        else:
            return caption


# Local Variables:
# mode:python
# fill-column:80
# End:
