#!/usr/bin/python
#
# IPCini.py
# Description: IPC ini configuration files wrapper
# -----------------------------------------------------------------------------
#
# Started on  <Mon Feb 14 10:32:19 2011 Carlos Linares Lopez>
# Last update <Saturday, 03 December 2011 22:59:05 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPCini.py 308 2011-12-20 23:08:29Z clinares                          $
# $Date:: 2011-12-21 00:08:29 +0100 (Wed, 21 Dec 2011)                       $
# $Revision:: 308                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
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
IPC ini configuration files wrapper
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.2'
__revision__ = '$Revision: 308 $'

# imports
# -----------------------------------------------------------------------------
import configobj                        # ini configuration files

# -----------------------------------------------------------------------------
# IPCini
#
#     This class implements a wrapper to access the IPC ini
#     configuration files
# -----------------------------------------------------------------------------
class IPCini:
    """
    This class implements a wrapper to access the IPC ini
    configuration files
    """

    # default constructor
    def __init__ (self, bookmark):
        """
        default constructor
        """

        # copy the attribute
        self._bookmark = bookmark

        # initialization
        self._tracks = []
        self._subtracks = {}
        self._planners = {}
        self._domains = {}

        # create the configobj entry point
        try:
            self._configobj = configobj.ConfigObj (bookmark, file_error = True, indent_type = '\t')
        except:
            print """
 [Error: ini configuration file '%s' not found]
""" % bookmark
            raise IOError

        
    # methods

    # return the name of the IPC
    def get_name (self):
        """
        return the name of the IPC
        """

        try:
            return self._configobj ['name']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the name of the IPC]
"""
        

    # return the part of the IPC
    def get_part (self):
        """
        return the part of the IPC
        """

        try:
            return self._configobj ['part']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the part of the IPC]
"""
        

    # return the svn bookmark
    def get_svn (self):
        """
        return the svn bookmark
        """

        try:
            return self._configobj ['general']['svn']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the svn bookmark]
"""
            raise IOError


    # return the wiki home address
    def get_wiki (self):
        """
        return the wiki home address
        """

        try:
            return self._configobj ['general']['wiki']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the wiki home address]
"""
        

    # return the mail user
    def get_mailuser (self):
        """
        return the mail user
        """

        try:
            return self._configobj ['general']['mailuser']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the mail user]
"""
            raise KeyError
        

    # return the mail password
    def get_mailpwd (self):
        """
        return the mail password
        """

        try:
            return self._configobj ['general']['mailpwd']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the mail password]
"""
            raise KeyError
        

    # return the smtp server
    def get_smtp_server (self):
        """
        return the smtp server
        """

        try:
            return self._configobj ['general']['smtp server']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the smtp server]
"""
            raise KeyError
        

    # return the smtp port
    def get_smtp_port (self):
        """
        return the smtp port
        """

        try:
            return self._configobj ['general']['smtp port']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the smtp port]
"""
            raise KeyError
        

    # return the cluster front-end user@computer
    def get_cluster (self):
        """
        return the cluster front-end user@computer
        """

        try:
            return self._configobj ['general']['cluster']
        except KeyError:
            print """
 [Error: it was not possible to retrieve the cluster front-end user@computer]
"""
        

    # show all tracks
    def get_tracks (self):
        """
        show all tracks
        """

        # only in case the tracks have not been retrieved before
        if (len (self._tracks) == 0):

            # read them from the ini file
            self._tracks = self._configobj ['tracks']['name']

            # initialize the subtracks of each track and its planners
            for itrack in self._tracks:
                self._subtracks [itrack] = []
                self._planners [itrack] = {}
                self._domains [itrack] = {}

        # return the _tracks
        return self._tracks


    # show all subtracks of a specific track
    def get_subtracks (self, track):
        """
        show all subtracks of a specific track
        """

        # sanity check - make sure that the specified track has been
        # already processed
        if (track not in self._tracks):
            self.get_tracks ()

            # if the requested track is still unknown
            if (track not in self._tracks):

                # then raise an exception
                raise ValueError, " The track '%s' has not been found in the INI configuration file '%s'" % (track, self._bookmark)

        # only in case the tracks have not been retrieved before
        if (len (self._subtracks [track]) == 0):

            # read them from the ini file
            self._subtracks [track] = self._configobj [track]['subtracks']['name']

            # and now initialize the planners of this subtrack
            for isubtrack in self._subtracks [track]:
                self._planners [track][isubtrack] = []
                self._domains  [track][isubtrack] = []
            
        # return the subtracks
        return self._subtracks [track]


    # show all planners in a particular track/subtrack
    def get_planners (self, track, subtrack):
        """
        show all planners in a particular track/subtrack
        """

        # sanity check - make sure that the specified track/subtrack is known
        if (track not in self._tracks or subtrack not in self._subtracks [track]):
            self.get_subtracks (track)

            # if the requested track is still unknown
            if (track not in self._tracks or subtrack not in self._subtracks [track]):

                # then raise an exception
                raise ValueError, " The track-subtrack '%s-%s' has not been found in the INI configuration file '%s'" % (track, subtrack, self._bookmark)

        # only in case the planners have not been retrieved before
        if (len (self._planners [track][subtrack]) == 0):

            # read them from the ini file
            self._planners [track][subtrack] = self._configobj [track][subtrack]['planners']['name']

        # return the planners
        return self._planners [track][subtrack]


    # show all domains in a particular track/subtrack
    def get_domains (self, track, subtrack):
        """
        show all domains in a particular track/subtrack
        """

        # sanity check - make sure that the specified track/subtrack is known
        if (track not in self._tracks or subtrack not in self._subtracks [track]):
            self.get_subtracks (track)

            # if the requested track is still unknown
            if (track not in self._tracks or subtrack not in self._subtracks [track]):

                # then raise an exception
                raise ValueError, " The track-subtrack '%s-%s' has not been found in the INI configuration file '%s'" % (track, subtrack, self._bookmark)

        # only in case the domains have not been retrieved before
        if (len (self._domains [track][subtrack]) == 0):

            # read them from the ini file
            self._domains [track][subtrack] = self._configobj [track][subtrack]['domains']['name']

        # return the domains
        return self._domains [track][subtrack]



# Local Variables:
# mode:python
# fill-column:80
# End:
