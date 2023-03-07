#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# argtools.py
# Description: Definition of actions to be used by argparse
# -----------------------------------------------------------------------------
#
# Started on  <Mon Nov 14 21:21:56 2011 Carlos Linares Lopez>
# Last update <Monday, 14 November 2011 21:25:13 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id::                                                                      $
# $Date::                                                                    $
# $Revision::                                                                $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@ubuntu>
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
Definition of actions to be used by argparse
"""

__version__  = '1.2'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options

# -----------------------------------------------------------------------------
# AppendAction
#
# this class provides a slightly modified behaviour for appending
# values to a given attribute in argparse. If no item was previously
# stored, it takes the input list, otherwise, it just adds (instead of
# appending) the incoming list
# -----------------------------------------------------------------------------

class AppendAction (argparse.Action):

    """
    this class provides a slightly modified behaviour for appending
    values to a given attribute in argparse. If no item was previously
    stored, it takes the input list, otherwise, it just adds (instead of
    appending) the incoming list
    """

    def __call__ (self, parser, namespace, values, option_string=None):
        """
        make this class callable so that it can be directly used from
        argparse in the usual form 'action=AppendAction'
        """

        # if there was no value previously stored
        if (not vars (namespace) [self.dest]):

            # then initialize its contents
            setattr (namespace, self.dest, values)
        else:

            # otherwise, augment the current list with the new one
            setattr (namespace, self.dest, vars (namespace) [self.dest] + values)



# Local Variables:
# mode:python
# fill-column:80
# End:
