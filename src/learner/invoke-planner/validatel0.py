#!/usr/bin/python
#
# validatel0.py
# Description: Validation of the solution generated at the level of a
# particular problem
# -----------------------------------------------------------------------------
#
# Started on  <Fri May 13 15:55:49 2011 Carlos Linares Lopez>
# Last update <Monday, 14 November 2011 23:10:53 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: validatel0.py 307 2011-11-14 22:17:56Z clinares                      $
# $Date:: 2011-11-14 23:17:56 +0100 (Mon, 14 Nov 2011)                       $
# $Revision:: 307                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@Ceres.local>
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
Validation of the solution generated at the level of a particular problem
"""

__version__  = '1.2'
__revision__ = '$Revision: 307 $'
__date__     = '$Date: 2011-11-14 23:17:56 +0100 (Mon, 14 Nov 2011) $'


# imports
# -----------------------------------------------------------------------------
import datetime         # date/time
import fnmatch          # filename matching services
import getopt           # variable-length params
import getpass          # getuser
import logging          # loggers
import os               # path and process management
import re               # regular expressions
import socket           # gethostname
import subprocess       # for invoking val and reading its output
import stat             # stat constants
import sys              # argv, exit
import time             # time mgmt

import IPClog           # IPC log files

import PrettyTable      # beautified ascii output

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.2"

LOGDICT = {'node': socket.gethostname (),       # extra data to be passed
           'user': getpass.getuser ()}          # to loggers

# LOGREGEXP = '_(?P<track>[a-z]+)-(?P<subtrack>[a-z]+)\.(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-log'
LOGREGEXP = '_(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-log'
OKVAL = '^Plan valid.*'
FINALVALUE = '^Final value: (?P<value>[0-9\.]+) (?P<length>[0-9]+)'
KOVAL = '^Failed.*'

# the VAL executable
VAL = 'validate'

# flags from VAL
FAIL, SUCCESS = range (0,2)

# -----------------------------------------------------------------------------

# Funcs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params
# -----------------------------------------------------------------------------
def show_switches (directory):

    """
    show a somehow beautified view of the current params
    """

    # logger settings
    logger = logging.getLogger('validatel0::show_switches')

    logger.info (""" -----------------------------------------------------------------------------
 * directory : %s
 -----------------------------------------------------------------------------\n""" % (directory),
                 extra=LOGDICT)


# -----------------------------------------------------------------------------
# createlogger
#
# opens a file in write mode in case a logfile is given. If not, it creates a
# basic logger. Messages above the given level are issued.
#
# it returns the name of the logfile recording all logrecords. If none has been
# created it returns the empty string
# -----------------------------------------------------------------------------
def createlogger (logfile, level):

    """
    opens a file in write mode in case a logfile is given. If not, it creates a
    basic logger. Messages above the given level are issued

    it returns the name of the logfile recording all logrecords. If none has
    been created it returns the empty string
    """

    # create the log file either as a file stream or to the stdout
    if (logfile):

        # substitute the placeholders in logfile accordingly
        logfilename = logfile
        logging.basicConfig (filename=logfilename, filemode = 'w', level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s") 

    else:
        logfilename = ''
        logging.basicConfig (level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")

    # and return the logfilename
    return logfilename


# -----------------------------------------------------------------------------
# checkflags
#
# check the parameters provided by the user
# -----------------------------------------------------------------------------
def checkflags (directory):

    """
    check the parameters provided by the user
    """

    # logger settings
    logger = logging.getLogger('validatel0::checkflags')

    # check a directory has been provided
    if (directory == ""):
        logger.critical ("""
 Please provide a location with the domain, problem and solution files to validate
 Type '%s --help' for more information
""" % PROGRAM_NAME, extra=LOGDICT)
        raise ValueError

    # check now that the specified directory exists indeed
    if (not os.path.exists (directory)):
        logger.critical ("""
 The directory given with --directory (%s) does not exist!
 Type '%s --help' for more information
""" % (directory, PROGRAM_NAME), extra=LOGDICT)
        raise ValueError


# -----------------------------------------------------------------------------
# which
#
# mimics the behaviour of the which unix command by looking the location of an
# executable or None if it does not exist
#
# (taken from stackoverflow.com)
# -----------------------------------------------------------------------------
def which (program):

    """
    mimics the behaviour of the which unix command by looking the location of an
    executable or None if it does not exist
    """

    # the following subfunction checks that the given path points to a location
    # that exists and that can be executed
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    # get both the path and name of the program
    fpath, fname = os.path.split(program)

    # in case a path was given
    if fpath:

        # check it and if it exists and can be run, return it
        if is_exe (program):
            return program

    # otherwise
    else:

        # examine the PATH environ and check that this program exists in one of
        # those locations
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    # It was not found, so return None
    return None


# -----------------------------------------------------------------------------
# checkval
#
# checks that the Automatic Validation Tool from the University of Stratchclyde
# is available in the system. If not, it exits with an error message
# -----------------------------------------------------------------------------
def checkval ():

    """
    checks that the Automatic Validation Tool from the University of Stratchclyde
    is available in the system. If not, it exits with an error message
    """

    # logger settings
    logger = logging.getLogger('validatel0::checkval')

    # check whether VAL is available or not
    if (not which (VAL)):

        logger.critical("""
 The Automatic Validation Tool for PDDL has not been found in this system 
 Donwload version 4.2.09 or newer from:

      www.plg.inf.uc3m.es/ipc2011-deterministic/FrontPage/Software 

 install it and make sure that your PATH points to its location
""", extra=LOGDICT)
        raise IOError


# -----------------------------------------------------------------------------
# checkdepth0
#
# checks the specified directory to make sure that it contains the minimal
# number of files that identify it as a depth0 directory
#
# if 'error' is given, an error message is issued when a given file is not found
# -----------------------------------------------------------------------------
def checkdepth0 (directory, error=True):

    """
    checks the specified directory to make sure that it contains the minimal
    number of files that identify it as a depth0 directory
    
    if 'error' is given, an error message is issued when a given file is not found
    """

    # logger settings
    logger = logging.getLogger('validatel0::checkdepth0')

    # the minimal files are the '-log' file and the pddl files
    if ('domain.pddl' not in os.listdir (directory)):
        if error:
            logger.critical (" Domain file 'domain.pddl' has not been found in %s" % directory,
                             extra=LOGDICT)
        raise KeyError, 'domain.pddl'

    if ('problem.pddl' not in os.listdir (directory)):
        if error:
            logger.critical ("Problem file 'problem.pddl' has not been found in %s""" % directory,
                             extra=LOGDICT)
        raise KeyError, 'problem.pddl'

    # look for the log file
    logfile = filter (lambda x : re.match(LOGREGEXP,x), os.listdir (directory))

    if (len (logfile) == 0):
        if error:
            logger.critical (" No '-log' file has been found at %s" % directory,
                             extra=LOGDICT)
        raise KeyError, 'problem.pddl'

    if (len (logfile) > 1):
        if error:
            logger.critical (" More than one '-log' file has been found at %s: %s" % (directory, logfile),
                             extra=LOGDICT)
        raise IndexError, logfile

    # Now, all the essential files have been found an a new log file with the
    # information of the validation shall be generated
    m = re.match (LOGREGEXP, logfile [0])
    return (m.group ('planner'), m.group ('domain'), m.group ('problem'))


# -----------------------------------------------------------------------------
# checkoutput
#
# check the output of the val utility. It returns a tuple signaling whether the
# plan was successful or not and the final value and the step length ---which is
# -1 in case of failure
# -----------------------------------------------------------------------------
def checkoutput (lines):
    """
    check the output of the val utility. It returns a tuple signaling whether
    the plan was successful or not and the final value and the step length
    ---which is -1 in case of failure
    """

    # logger settings
    logger = logging.getLogger('validatel0::checkoutput')

    # look first for successful plans
    success = filter (lambda x : re.match (OKVAL, x), lines)

    # if none is found, check whether the plan was not successful
    if (len (success) == 0):
        failed = filter (lambda x : re.match (KOVAL, x), lines)

        # if it is not failed, the raise an error
        if (len (failed) == 0):
            logger.critical (""" The plan was not found to be either successful or failed
 Current output from VAL:
 %s
""" % lines, extra=LOGDICT)
            raise ValueError

        # otherwise, return a tuple signaling a failed plan
        return (FAIL, -1, -1)

    # At this point, the plan is known to be successful, so look for the final
    # cost
    cost = filter (lambda x : re.match (FINALVALUE, x), lines)

    if (len (cost) == 0):
        logger.critical (" No line was found with the final value in the output of VAL",
                         extra=LOGDICT)
        raise ValueError

    if (len (cost) > 1):
        logger.critical ("""
 More than one line with the final value has been found in the output of VAL
 Offending lines are:
 %s
""" % cost, extra=LOGDICT)
        raise ValueError

    # and return success with the final cost
    return (SUCCESS,
            re.match (FINALVALUE, cost [0]).group ('value'),
            re.match (FINALVALUE, cost [0]).group ('length'))


# -----------------------------------------------------------------------------
# validate0
#
# validates all the solution files that have been generated at this depth 0
# directory
#
# if 'error' is given, an error message is issued when a file is missing
#
# it returns the number of solution files validated and the number of them that
# were found successful
# -----------------------------------------------------------------------------
def validate0 (directory, verbose=False, error=True):

    """
    validates all the solution files that have been generated at this depth 0
    directory

    if 'error' is given, an error message is issued when a file is missing

    it returns the number of solution files validated and the number of them
    that were found successful
    """

    # return a negative number, zero or a positive number if first is less than,
    # equal or greater than second. In order to perform the comparison, the
    # number of characters in first and second are taken into account as well
    def __cmpfiles (first, second):
        if (first == second):
            return 0
        return {False: +1, True: -1} [len (first) < len (second) or 
                                      (len (first) == len (second) and (first < second))]


    # logger settings
    logger = logging.getLogger('validatel0::validatel0')

    # in case verbose output has been requested, show the current directory
    if (verbose):
        logger.info (" Processing directory '%s'" % directory, extra=LOGDICT)

    # check this is a level0 directory, if so, retrieve its params
    try:
        (planner, domain, problem) = checkdepth0 (directory, error)
    except KeyError, message:
        if (error):
            raise KeyError, message
    except IndexError, message:
        if (error):
            raise IndexError, message

    # first, create the val log file
    valfile = '_' + planner + '-' + domain + '.' + problem + '-val'
    vallog = IPClog.IPClog (directory + '/' + valfile)
    vallog.write ("\n\n")
 
    # second, get the number of solution files in this directory
    correct = nbsolfiles = 0            # number of successful plans/solution files
    prefix = "plan.soln"                # prefix of all solution files
    solfiles = sorted (fnmatch.filter (os.listdir (directory), prefix + '*'),
                       cmp=__cmpfiles)

    # finally, write the val log file with the number of solution files found
    # and the result of the automated validation - count also the number of
    # validated solutions found
    if (len (solfiles) == 0):
        vallog.write ("\n\n Number of solution files found: 0\n")
        vallog.write (" Number of correct solutions found: 0\n\n")

        if (verbose):
            logger.info (""" Number of solution files found: 0
 Number of correct solutions found: 0""", extra=LOGDICT)
            
    else:

        # for each solution file
        for isolfile in solfiles:

            # make sure that this file is not empty ---unfortunately, some
            # planners do that
            solsize = os.stat (directory + '/' + isolfile) [stat.ST_SIZE]

            # only in case the file is not empty
            if (solsize > 0):

                # launch the automated validation and capture the standard output,
                # the standard error and the return value
                valprocess = subprocess.Popen ([VAL, "-L", "-t", "0.000005", 
                                                directory + '/' + "domain.pddl", 
                                                directory + '/' + "problem.pddl", 
                                                directory + '/' + isolfile], 
                                               bufsize=-1, stdout=subprocess.PIPE, 
                                               stderr=subprocess.PIPE)

                # wait for the validation to terminate so that the return code can
                # be captured
                valprocess.wait ()
                try:
                    (status, value, length) = checkoutput (valprocess.stdout.readlines ())
                except:
                    logger.critical(" Fatal Error in directory '%s'" % directory, extra=LOGDICT)
                    raise IOError

                vallog.write ( " Solution file: %s\n" % isolfile )
                vallog.write ( " Size         : %i\n" % solsize)
                vallog.write ( " Status       : %s\n" % status )
                vallog.write ( " Value        : %s\n" % value )
                vallog.write ( " Step length  : %s\n" % length )
                vallog.write ( " return code  : %s\n" % valprocess.returncode )
                vallog.write ( " stderr       : %s\n\n" % valprocess.stderr.readlines ())

                if (verbose):
                    logger.info ( """ Solution file: %s
 Size         : %i
 Value        : %s
 Step length  : %s""" % (isolfile, solsize, value, length), extra=LOGDICT)

                # increment the number of solution files processed
                nbsolfiles += 1
                
                # count the number of correct solutions found so far
                if (status == SUCCESS):
                    correct += 1

            # otherwise note this explicitly in the vallog
            else:

                vallog.write ( " Solution file: %s\n" % isolfile )
                vallog.write ( " Size         : %i [skipped]\n\n" % solsize)

                if (verbose):
                    logger.info ( """ Solution file: %s
 Size         : %i [skipped]\n\n""" % (isolfile, solsize), extra=LOGDICT)

        # print the number of correct solutions found so far before exiting
        vallog.write (" Number of solution files found: " + str (nbsolfiles) + "\n")
        vallog.write (" Number of correct solutions found: " + str (correct) + "\n\n")

    # close the log val file
    vallog.close ()

    # finally, return the number of solution files validated and how many were
    # found to be successful
    return (nbsolfiles, correct)


# -----------------------------------------------------------------------------
# show_output
#
# shows a table with a unique row that contains the number of solution files
# validated and how many were found to be successful
# -----------------------------------------------------------------------------
def show_output (nbfiles, nbsuccessful):

    """
    shows a table with a unique row that contains the number of solution files
    validated and how many were found to be successful
    """

    # logger settings
    logger = logging.getLogger('validatel0::show_output')

    # create a pretty table
    table = PrettyTable.PrettyTable (["# solution files", "# successful plans"])
    
    # write the only row or data
    table.add_row ([nbfiles, nbsuccessful])

    # and show it
    logger.info('%s' % table, extra=LOGDICT)



# Local Variables:
# mode:python
# fill-column:80
# End:
