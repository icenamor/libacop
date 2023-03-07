#!/usr/bin/python
#
# check.py
# Description: Checks that planners beneath a given directory seem to be correct
# -----------------------------------------------------------------------------
#
# Started on  <Wed Jan 26 14:41:21 2011 Carlos Linares Lopez>
# Last update <Saturday, 03 December 2011 22:54:26 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: check.py 308 2011-12-20 23:08:29Z clinares                           $
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
Checks that planners beneath a given directory seem to be correct
"""

__version__  = '1.2'
__revision__ = '$Revision: 308 $'
__date__     = '$Date: 2011-12-21 00:08:29 +0100 (Wed, 21 Dec 2011) $'

# imports
# -----------------------------------------------------------------------------
import getopt           # variable-length params
import os               # files and directories mgmt
import re               # regular expressions
import sys              # argv, exit

import IPCData          # for managing IPC data

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.2"

# -----------------------------------------------------------------------------

# funcs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# decode
#
#     Returns:
#
#       the directory to examine. If none is provided, './' is used instead
#       questionnaire flag
#       recursive flag
# -----------------------------------------------------------------------------
def decode (argv):
    """
    Returns the directory to examine. If none is provided, './' is
    used instead
    questionnaire flag
    recursive flag
    """

    # Default values
    directory = './'
    questionnaire = False
    recursive = False

    # Process the argv command line
    try:
        options, args = getopt.getopt (argv, "d:aRhV",
                                       ["directory=", "questionnaire", "recursive",
                                        "help", "version"])
    except getopt.GetoptError:
        usage ()
        sys.exit (2)
    for arg, value in options:
        if arg in ("-h","--help"):                      # *** help
            usage ()
            sys.exit ()
        elif arg in ("-V","--version"):                 # *** version
            version ()
            sys.exit ()

        elif arg in ("-d", "--directory"):              # *** directory
            directory = os.path.normpath (value)

        elif arg in ("-q", "--questionnaire"):          # *** questionnaire
            questionnaire = True

        elif arg in ("-R", "--recursive"):              # *** recursive
            recursive = True

    # and return the parameters
    return (directory, questionnaire, recursive)

# -----------------------------------------------------------------------------
# usage
#
# shows the help banner
# -----------------------------------------------------------------------------
def usage ():

    """
    shows the help banner
    """
    
    print """
     %s - checks that planners beneath a given directory seem to be correct
     Usage: %s [OPTIONS]

        -d, --directory STRING     directory to examine. If noone is provided, '.' is
                                   used instead. Only the directories whose name matches
                                   the IPC naming convention (track-subtrack-name)
                                   are considered
        -q, --questionnaire        if provided, shows the PDDL Support Questionnaire

        -R, --recursive            if provided, subdirectories beneath the specified
                                   directory are examined as well ---false by default
                                   
        -h, --help                 display this help and exit
        -V, --version              output version information and exit

     """  % (PROGRAM_NAME, PROGRAM_NAME)

# -----------------------------------------------------------------------------
# version
#
# shows version info
# -----------------------------------------------------------------------------
def version ():

    """
    shows version info
    """

    print ("\n %s\n %s\n" % (__revision__[1:-1], __date__[1:-1]))
    print (" %s %s\n" % (PROGRAM_NAME, PROGRAM_VERSION))


# -----------------------------------------------------------------------------
# IPCmatch
#
# returns an objectmatch that results from the comparison with the IPC
# naming convention regular expression
# -----------------------------------------------------------------------------
def IPCmatch (str):

    """
    returns an objectmatch that results from the comparison with the
    IPC naming convention regular expression
    """

    return (re.match ("^[a-z]+-[a-z]+-[a-zA-Z0-9_-]+$",str))

# -----------------------------------------------------------------------------
# traverse
#
# traverses recursively the given directory until other subdirectories
# meeting the IPC naming convention are found or no subdirectories
# exist. All the directories found are returned in a list
# -----------------------------------------------------------------------------
def traverse (directory):

    """
    traverses recursively the given directory until other
    subdirectories meeting the IPC naming convention are found or no
    subdirectories exist. All the directories found are returned in a
    list
    """

    # base case: this directory meets the IPC naming convention:
    # track-subtrack-name
    m = IPCmatch (os.path.basename (directory))
    if (m != None):
        return [directory]

    # general case: this directory does not meet the IPC naming
    # convention so that its subdirectories shall be examined
    # ---getting rid of the hidden directories
    directories = []
    for icontent in os.listdir (directory):

        # compute the new subdirectory and traverse it in depth-first
        subdir = directory + '/' + icontent
        if (os.path.isdir (subdir) and icontent [0] != '.'):
            directories += traverse (subdir)
        
    # return all directories found so far
    return directories
    

# main
# -----------------------------------------------------------------------------
PROGRAM_NAME = sys.argv[0]              # get the program name

# decode switches
(DIRECTORY, QUESTIONNAIRE, RECURSIVE) = decode (sys.argv[1:])

# if a recursive flag has been set, get all the subdirs beneath the
# specified directory that meet the IPC naming convention
if (RECURSIVE):
    DIRECTORIES = traverse (DIRECTORY)

# otherwise, get the specified directory only if it matches the IPC
# naming convention
else:
    if (IPCmatch (os.path.basename (DIRECTORY))):
        DIRECTORIES = [DIRECTORY]
    else:
        DIRECTORIES = []

# Now, process all the directories one by one
NBPLANNERS = 0
for idirectory in DIRECTORIES:

    suffix = os.path.basename (idirectory)      # get the basename
    m = re.match ("^(?P<track>[a-z]+)-(?P<subtrack>[a-z]+)-(?P<name>[a-zA-Z0-9_-]+)$",suffix)

    # Now, create Planners with these dat
    try:
        planner = IPCData.IPCPlanner (m.group ('name'), m.group ('track'), \
                                      m.group ('subtrack'), idirectory)
    except IndexError, missing:
        print " [Fatal Error: file '%s' not found]" % (idirectory + '/' + str (missing))
        sys.exit (os.EX_NOINPUT)
        
    NBPLANNERS += 1

    # show the general information of this planner
    print "----------------------------------------------------------------------"
    print planner, "\n"

    # and now, in case the questionnaire has been requested, show it
    if (QUESTIONNAIRE):
        found = True
        try:
            planner.read_pddlsupportquestionnaire ()
        except IndexError, questionnaire:
            print " [Warning: file '%s' not found]"  % (idirectory + '/' + str(questionnaire))
            found = False
        if (found):
            planner.write_pddlsupportquestionnaire ()

# show overall reporting data
print """
 [%i planners found]
""" % NBPLANNERS



# Local Variables:
# mode:python
# fill-column:80
# End:
