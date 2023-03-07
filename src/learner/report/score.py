#!/usr/bin/env python
#
# score.py
# Description: computes the overall score tables per domain
# -----------------------------------------------------------------------------
#
# Started on  <Thu May 19 17:32:33 2011 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:10:09 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: score.py 321 2012-07-15 14:21:33Z clinares                           $
# $Date:: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012)                  $
# $Revision:: 321                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@Eris.local>
#

# -----------------------------------------------------------------------------
#     This file is part of IPCReport
#
#     IPCReport is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     IPCReport is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with IPCReport.  If not, see <http://www.gnu.org/licenses/>.
#
#     Copyright Carlos Linares Lopez, 2011
# -----------------------------------------------------------------------------

"""
computes the overall score tables per domain
"""

__version__  = '1.3'
__revision__ = '$Revision: 321 $'
__date__     = '$Date: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012) $'

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import datetime         # for printing current date and time
import getopt           # variable-length params
import math             # log10
import os               # path and process management
import re               # regular expressions
import sys              # argv, exit

from string import Template     # to use placeholders in the name of tables

import IPCrun           # runs data-handling
import report           # general facilities of the IPC reporting tools

import pyExcelerator.Workbook           # excel workbooks
import pyExcelerator.Style              # excel styles
import PrettyTable      # for generating pretty ascii tables

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.3"

UNSOLVED = -1
INVALID  = -2

# -----------------------------------------------------------------------------

# Funcs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# create_parser
#
# creates a command-line parser
# -----------------------------------------------------------------------------
def create_parser ():
    """
    creates a command-line parser
    """

    # create the parser
    parser = argparse.ArgumentParser (description="Computes the overall score tables per domain")
    
    # now, add the arguments
    
    # Group of alternative arguments
    alternative = parser.add_argument_group ("Alternative arguments", "The following arguments define alternative ways to access data. Note that it is not legal to use both arguments simultaneously but one has to be provided")
    alternative.add_argument ('-d', '--directory',
                              help='specifies a directory to explore')
    alternative.add_argument ('-s', '--summary',
                              help='reads a snapshot or summary previously generated with the option --summarize')
    
    # Group of filtering arguments
    filtering = parser.add_argument_group ("Filtering", "The following directives provide various means to filter the data to appear in the tables")
    filtering.add_argument ('-P', '--planner',
                            metavar='REGEXP',
                            default = '.*',
                            help='only planners meeting the specified regexp are considered. All by default')
    filtering.add_argument ('-D', '--domain',
                            metavar='REGEXP',
                            default = '.*',
                            help='only domains meeting the specified regexp are considered. All by default')
    filtering.add_argument ('-I', '--problem',
                            metavar='REGEXP',
                            default = '.*',
                            help='only problem ids meeting the specified regexp are examined. All by default')
    filtering.add_argument ('-t', '--time',
                            default=sys.maxint,
                            type=int,
                            help='computes the score tables in the interval [0, INTEGER]. By default, infinity')
    
    # Group of appearance arguments
    appearance = parser.add_argument_group ("Appearance", "The following arguments modify in one way or another how data is presented")
    appearance.add_argument ('-n','--name',
                             default='$track-$subtrack: $domain ($date)',
                             help="name of the output tables. A number of placeholders can be used that are substituted by their corresponding values. Accepted placeholders are $track, $subtrack, $domain, $date and $time. The default value is: '$track-$subtrack: $domain ($date)'")
    appearance.add_argument ('-m', '--metric',
                             default='quality',
                             choices=['quality', 'qt', 'solutions', 'time0', 'time1', 'time2'],
                             help='it specifies the metric to use when generating the overall score tables. Use --metrics to get a comprehensive list of the available metrics')
    appearance.add_argument ('-y', '--style',
                             default='table',
                             choices=['table','octave','html','excel','wiki','latex'],
                             help='sets the report style')
    
    # Group of miscellaneous arguments
    misc = parser.add_argument_group ('Miscellaneous')
    misc.add_argument ('-x','--metrics',
                       nargs=0,
                       action=ShowAction,
                       help='shows a comprehensive list of metrics recognized by this script')
    misc.add_argument ('-q','--quiet',
                       default=False,
                       action='store_true',
                       help='only prints the requested data')
    misc.add_argument ('-V', '--version',
                       action='version',
                       version=" %s %s %s %s" % (sys.argv [0], PROGRAM_VERSION, __revision__[1:-1], __date__[1:-1]),
                       help="output version information and exit")
    
    # and return the parser
    return parser


# -----------------------------------------------------------------------------
# ShowAction
#
# shows a comprehensive list of legal metrics recognized by this script. This
# is enclosed within a class definition to allow the automatic execution from
# the command-line parsing arguments
# -----------------------------------------------------------------------------
class ShowAction (argparse.Action):
    """
    shows a comprehensive list of legal metrics recognized by this
    script. This is enclosed within a class definition to allow the automatic
    execution from the command-line parsing arguments
    """

    def __call__(self, parser, namespace, values, option_string=None):

        print """
 This script acknowledges the following metrics:

   quality   - use the quality of the best solution
   qt        - use both quality and time and use the pareto dominance as a metric
   solutions - use the number of problems solved

 In the following metrics let T denote the time for a particular planner to solve a
 particular problem and let T* denote the best time among all planners

   time0     - compute the score as T*/T
   time1     - compute the score as 1/(1+log10(T/T*))
   time2     - compute the score as log10(1+T*)/log10(1+T) where T* is the best time 
               and T is the particular time for a domain/planner/problem
"""

        # and finally exit
        sys.exit (0)
        

# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params.
# -----------------------------------------------------------------------------
def show_switches (directory, summary, metric, name, planner, domain, problem, timebound, style):

    """
    show a somehow beautified view of the current params.
    """

    print (""" -----------------------------------------------------------------------------
 * %-14s : %s
 * metric         : %s
 * name           : %s
 * planner        : %s
 * domain         : %s
 * problem        : %s
 * timebound      : %s
 * style          : %s
 -----------------------------------------------------------------------------\n""" % ({False:'summary', True:'directory'}[bool (directory)], {False:summary, True:directory}[bool (directory)], metric, name, planner, domain, problem, {False:'infty', True:str(timebound)}[timebound<sys.maxint], style))


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
# checkflags
#
# check the parameters provided by the user
# -----------------------------------------------------------------------------
def checkflags (directory, summary):

    """
    check the parameters provided by the user
    """

    if (directory == "" and summary == ""):
        print """
 Please provide a location to explore with --directory or a summary to read with --summary
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    if (directory and summary):
        print """
 It is not legal to provide both a directory and a summary. Where should I read from?!
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    if (summary and (not os.access (summary, os.F_OK) or 
                     not os.access (os.path.dirname (summary), os.X_OK))):
        print """
 The summary file specified does not exist or it resides in an unreachable location
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    if (directory and (not os.path.exists(directory) or not os.access(directory, os.X_OK))):
        print """
 The directory specified either it does not exist of there are not privileges enough to access it
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError


# Helpers
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# initdata
#
# initializes the contents of the specified container with the given value
# -----------------------------------------------------------------------------
def initdata (key, value):

    """
    initializes the contents of the specified container with the given value
    """

    best = dict ()
    for ipair in zip (key, [value for ikey in key]):
        best [ipair[0]] = ipair[1]

    return best


# -----------------------------------------------------------------------------
# getvalue
#
# computes the best value returned by VAL for particular domain/planner/problem
# in the interval [0,timebound]. It takes special care of the unsolved/invalid
# problems and represent them accordingly
# -----------------------------------------------------------------------------
def getvalue (idomain, iplanner, iproblem, run, timebound = sys.maxint):

    """
    computes the best value returned by VAL for particular
    domain/planner/problem in the interval [0,timebound]. It takes special care
    of the unsolved/invalid problems and represent them accordingly
    """

    # retrieve the value computed by VAL for this particular
    # instance of domain/planner/problem
    key = iplanner + IPCrun.CHAR_SEP + idomain + IPCrun.CHAR_SEP + iproblem
    try:

        # first, check whether this problem was solved or not
        if (run [key, IPCrun.SOLVED]):

            # next, check if the solutions are valid according to
            # VAL
            if (run [key, IPCrun.OKSOLVED]):

                # ok, so at least one solution was generated ---retrieve the
                # best solution found in a time less or equal than timebound. If
                # none is found, mark this problem as unsolved within the given
                # time interval
                values = [ivalue[0] for ivalue in zip (run[(key, IPCrun.VALUES)],
                                                       run[(key, IPCrun.OKTIMESOLS)])
                          if ivalue[1] <= timebound]
                if (values):
                    value = min (values)
                else:
                    value = UNSOLVED

            else:

                # otherwise, the solution is invalid!
                value = INVALID

        else:

            # at this point, no solution was found
            value = UNSOLVED

    # if a KeyError happened is because this (key,var) is not stored at this
    # run. The more likely reason is that this directory has not been validated
    # so issue an exception warning the use
    except:
        raise ValueError, """
 Fatal Error - It was not possible to retrieve data from problem '%s', domain '%s' for planner '%s'
               The most likely reason is that these solutions have not been validated or maybe
               this directory does not exist!
 """ % (iproblem, idomain, iplanner)

    # finally, return the value computed so far
    return value


# -----------------------------------------------------------------------------
# getscore
#
# computes the score (the ratio between the best value and the current value)
# for a particular domain/planner/problem. It takes special care of the
# unsolved/invalid problems and represent them accordingly
# -----------------------------------------------------------------------------
def getscore (idomain, iplanner, iproblem, values, best):

    """
    computes the score (the ratio between the best value and the current value)
    for a particular domain/planner/problem. It takes special care of the
    unsolved/invalid problems and represent them accordingly
    """

    # in case a best value is available for this
    # domain/planner/problem
    if (best[idomain][iproblem] != UNSOLVED and 
        values[idomain][iplanner][iproblem] > 0):

        score = float (best [idomain][iproblem]) / values [idomain][iplanner][iproblem]

    # otherwise, no score can be assigned to this domain/planner/problem since
    # nobody was "scored" by VAL. Now, check whether this particular problem was
    # unsolved or invalid
    else:

        score = values [idomain][iplanner][iproblem]

    # and return the score computed so far
    return score


# -----------------------------------------------------------------------------
# getscoreqt
#
# computes the score (the ratio between the current value and the best value)
# for a particular domain/planner/problem. It takes special care of the
# unsolved/invalid problems and represent them accordingly
# -----------------------------------------------------------------------------
def getscoreqt (idomain, iplanner, iproblem, values, best):

    """
    computes the score (the ratio between the current value and the best value)
    for a particular domain/planner/problem. It takes special care of the
    unsolved/invalid problems and represent them accordingly
    """

    # in case a best value is available for this
    # domain/planner/problem
    if (best[idomain][iproblem] > 0):

        score = float (values [idomain][iplanner][iproblem]) / best [idomain][iproblem]

    # else, if there is no best value or the problem has not been solved, copy
    # it to the resulting score
    else:

        score = values [idomain][iplanner][iproblem]

    # and return the score computed so far
    return score


# -----------------------------------------------------------------------------
# gettiming
#
# computes the timing of the last solution generated so far for a particular
# domain/planner/problem in the interval [0, timebound]. It takes special care
# of the unsolved/invalid problems and represent them accordingly
# -----------------------------------------------------------------------------
def gettiming (idomain, iplanner, iproblem, run, timebound = sys.maxint):

    """
    computes the timing of the last solution generated so far for a particular
    domain/planner/problem in the interval [0, timebound]. It takes special care
    of the unsolved/invalid problems and represent them accordingly
    """

    # retrieve the time of the last solution for this particular instance of
    # domain/planner/problem
    key = iplanner + IPCrun.CHAR_SEP + idomain + IPCrun.CHAR_SEP + iproblem
    try:

        # first, check whether this problem was solved or not
        if (run [key, IPCrun.SOLVED]):

            # next, check if the solutions are valid according to
            # VAL
            if (run [key, IPCrun.OKSOLVED]):

                # now, make sure there is at least one solution generated before
                # the timebound
                if (run[(key, IPCrun.OKTIMESOLS)] [0] <= timebound):

                    # everything went fine, so retrieve the largest value of all the
                    # time stamps when this planner generated valid solutions
                    value = max ([itime for itime in run[(key, IPCrun.OKTIMESOLS)]
                                  if itime <= timebound])

                # ... if not, return a very high value ---this makes sense for
                # those cases where time-based metrics use this value in the
                # denominator so that the quotient will be equal to 0 in
                # practice
                else:
                    value = sys.maxint

            else:

                # otherwise, the solution is invalid!
                value = INVALID

        else:

            # at this point, no solution was found
            value = UNSOLVED

    # if a KeyError happened is because this (key,var) is not stored at this
    # run. The more likely reason is that this directory has not been validated
    # so issue an exception warning the use
    except:
        raise ValueError, """
 Fatal Error - It was not possible to retrieve data from problem '%s', domain '%s' for planner '%s'
               The most likely reason is that these solutions have not been validated or maybe
               this directory does not exist!
 """ % (iproblem, idomain, iplanner)

    # finally, return the value computed so far
    return value


# -----------------------------------------------------------------------------
# gettimescore0
#
# computes the score (the ratio between the best value and the current value)
# for a particular domain/planner/problem. It takes special care of the
# unsolved/invalid problems and represent them accordingly
# -----------------------------------------------------------------------------
def gettimescore0 (idomain, iplanner, iproblem, values, best):

    """
    computes the score (the ratio between the best value and the current value)
    for a particular domain/planner/problem. It takes special care of the
    unsolved/invalid problems and represent them accordingly
    """

    # if the current time is 0, then it gets the maximum score: 1.0
    if (values [idomain][iplanner][iproblem] == 0):
        score = 1.0

    # if it is not 0, but someone else made it in 0, then this one gets the
    # lowest score: 0.0
    elif (values [idomain][iplanner][iproblem] > 0 and 
          best[idomain][iproblem] == 0):
        score = 0.0

    # otherwise, in case a best value is available for this
    # domain/planner/problem
    elif (best[idomain][iproblem] != UNSOLVED and 
          values[idomain][iplanner][iproblem] > 0):

        score = float (best [idomain][iproblem]) / values [idomain][iplanner][iproblem]

    # finally, no score can be assigned to this domain/planner/problem. Now,
    # check whether this particular problem was unsolved or invalid
    else:

        score = values [idomain][iplanner][iproblem]

    # and return the score computed so far
    return score


# -----------------------------------------------------------------------------
# gettimescore1
#
# computes the score as 1/1+log (T/T*) where T is the time for this particular
# domain/planner/problem and T* is the best across all planners. In particular,
# all times T below 1 sec are considered to be equal to 1 sec ---and hence this
# differences to be irrelevant.
#
# It takes special care of the unsolved/invalid problems and represent them
# accordingly
# -----------------------------------------------------------------------------
def gettimescore1 (idomain, iplanner, iproblem, values, best):

    """
    computes the score as 1/1+log (T/T*) where T is the time for this particular
    domain/planner/problem and T* is the best across all planners. In
    particular, all times T below 1 sec are considered to be equal to 1 sec
    ---and hence this differences to be irrelevant.
    
    It takes special care of the unsolved/invalid problems and represent them
    accordingly
    """

    # make the necessary corrections to the best time and this time
    if (values [idomain][iplanner][iproblem] >= 0 and
        values [idomain][iplanner][iproblem] <= 1):
        t = 1
    else:
        t = values [idomain][iplanner][iproblem]

    if (best [idomain][iproblem] >= 0 and
        best [idomain][iproblem] <= 1):
        bestt = 1
    else:
        bestt = best [idomain][iproblem]

    # in case a best value is available for this domain/planner/problem
    if (bestt != UNSOLVED and 
          t >= 1):

        score = 1/(1+math.log10(float (t)/bestt))

    # otherwise, no score can be assigned to this domain/planner/problem. Now,
    # check whether this particular problem was unsolved or invalid
    else:

        score = values [idomain][iplanner][iproblem]

    # and return the score computed so far
    return score


# -----------------------------------------------------------------------------
# gettimescore2
#
# computes the score as log (1+T*)/log(1+T) where T is the time for this
# particular domain/planner/problem and T* is the best across all planners. In
# particular, all times T below 1 sec are considered to be equal to 1 sec ---and
# hence this differences to be irrelevant.
#
# It takes special care of the unsolved/invalid problems and represent them
# accordingly
# -----------------------------------------------------------------------------
def gettimescore2 (idomain, iplanner, iproblem, values, best):

    """
    computes the score as log (1+T*)/log(1+T) where T is the time for this
    particular domain/planner/problem and T* is the best across all planners. In
    particular, all times T below 1 sec are considered to be equal to 1 sec
    ---and hence this differences to be irrelevant.
    
    It takes special care of the unsolved/invalid problems and represent them
    accordingly
    """

    # make the necessary corrections to the best time and this time
    if (values [idomain][iplanner][iproblem] >= 0 and
        values [idomain][iplanner][iproblem] <= 1):
        t = 1
    else:
        t = values [idomain][iplanner][iproblem]

    if (best [idomain][iproblem] >= 0 and
        best [idomain][iproblem] <= 1):
        bestt = 1
    else:
        bestt = best [idomain][iproblem]

    # in case a best value is available for this domain/planner/problem
    if (bestt != UNSOLVED and 
          t >= 1):

        score = math.log10(1+bestt)/math.log10 (1+t)

    # otherwise, no score can be assigned to this domain/planner/problem. Now,
    # check whether this particular problem was unsolved or invalid
    else:

        score = values [idomain][iplanner][iproblem]

    # and return the score computed so far
    return score


# -----------------------------------------------------------------------------
# getsolution
#
# computes whether a problem was solved according to VAL for a particular
# domain/planner/problem in the interval [0, timebound]. It takes special care
# of the unsolved/invalid problems and represent them accordingly
# -----------------------------------------------------------------------------
def getsolution (idomain, iplanner, iproblem, run, timebound = sys.maxint):

    """
    computes whether a problem was solved according to VAL for a particular
    domain/planner/problem in the interval [0, timebound]. It takes special care
    of the unsolved/invalid problems and represent them accordingly
    """
    
    # retrieve the value computed by VAL for this particular
    # instance of domain/planner/problem
    key = iplanner + IPCrun.CHAR_SEP + idomain + IPCrun.CHAR_SEP + iproblem
    try:
        
        # first, check whether this problem was solved or not
        if (run [key, IPCrun.SOLVED]):
            
            # next, check if the solutions are valid according to
            # VAL
            if (run [key, IPCrun.OKSOLVED]):
                
                # everything went fine, so check whether this planner solved
                # this problem/domain in the given time interval or not
                timings = [itime for itime in run[(key, IPCrun.OKTIMESOLS)] \
                           if itime <= timebound]
                value = {False: UNSOLVED, True: 1}[len (timings) > 0]
                
            else:
                
                # otherwise, the solution is invalid!
                value = INVALID
                
        else:
                
            # at this point, no solution was found
            value = UNSOLVED
                
                # if a KeyError happened is because this (key,var) is not stored at this
    # run. The more likely reason is that this directory has not been validated
    # so issue an exception warning the use
    except:
        raise ValueError, """
 Fatal Error - It was not possible to retrieve data from problem '%s', domain '%s' for planner '%s'
               The most likely reason is that these solutions have not been validated or maybe
               this directory does not exist!
 """ % (iproblem, idomain, iplanner)

    # finally, return the value computed so far
    return value


# -----------------------------------------------------------------------------
# getqt
#
# computes the tuple (quality, time) for a particular domain/planner/problem in
# the interval [0, timebound]. It takes special care of the unsolved/invalid
# problems and represent them accordingly
# -----------------------------------------------------------------------------
def getqt (idomain, iplanner, iproblem, run, timebound = sys.maxint):

    """
    computes the tuple (quality, time) for a particular domain/planner/problem
    in the interval [0, timebound]. It takes special care of the
    unsolved/invalid problems and represent them accordingly
    """

    # retrieve the value computed by VAL for this particular
    # instance of domain/planner/problem
    key = iplanner + IPCrun.CHAR_SEP + idomain + IPCrun.CHAR_SEP + iproblem
    try:
        
        # first, check whether this problem was solved or not
        if (run [key, IPCrun.SOLVED]):

            # next, check if the solutions are valid according to
            # VAL
            if (run [key, IPCrun.OKSOLVED]):

                # ok, so at least one solution was generated ---retrieve the
                # best solution found in a time less or equal than timebound. If
                # none is found, mark this problem as unsolved within the given
                # time interval
                tuples = filter (lambda x:x[1] <= timebound,
                                 zip (run[(key, IPCrun.VALUES)], run[(key, IPCrun.OKTIMESOLS)]))
                if (tuples):
                    value = min (tuples)
                else:
                    value = UNSOLVED

            else:

                # otherwise, the solution is invalid!
                value = INVALID
                
        else:

            # at this point, no solution was found
            value = UNSOLVED

    # if a KeyError happened is because this (key,var) is not stored at this
    # run. The more likely reason is that this directory has not been validated
    # so issue an exception warning the use
    except:
        raise ValueError, """
 Fatal Error - It was not possible to retrieve data from problem '%s', domain '%s' for planner '%s'
               The most likely reason is that these solutions have not been validated or maybe
               this directory does not exist!
 """ % (iproblem, idomain, iplanner)
        sys.exit ()

    # finally, return the value computed so far
    return value


# -----------------------------------------------------------------------------
# getparetodominance
#
# computes the number of entries pareto dominanted by (iplanner/iproblem) in a
# given idomain across all iplanners in the same idomain. It receives a matrix
# (as a dictionary of dictionaries) of tuples whose 'planners' are assumed to be
# the second key
# -----------------------------------------------------------------------------
def getparetodominance (idomain, iplanner, iproblem, matrix, planners):

    """
    computes the number of entries pareto dominanted by (iplanner/iproblem) in a
    given idomain across all iplanners in the same idomain. It receives a matrix
    (as a dictionary of dictionaries) of tuples whose 'planners' are assumed to
    be the second key
    """

    # initialization
    dominance = 0

    # if this (domain/planner/problem) does not have a tuple, then it cannot
    # dominate anyone
    if (matrix[idomain][iplanner][iproblem] != UNSOLVED and
        matrix[idomain][iplanner][iproblem] != INVALID):

        # traverse all keys in the matrix
        for ikey in planners:

            # only in case this is not the planner currently under consideration
            if (ikey != iplanner):

                # if this other planner did not solved the problem, then it is
                # pareto-dominated by this one
                if (matrix[idomain][ikey][iproblem] == UNSOLVED or
                    matrix[idomain][ikey][iproblem] == INVALID):

                    dominance += 1

                # otherwise, compare both tuples
                else:
                
                    cmpvalue = cmppareto (matrix[idomain][iplanner][iproblem],
                                          matrix[idomain][ikey][iproblem])

                    # if this (iplanner/iproblem) is pareto-dominated by this
                    # (key/iproblem) then it has both more quality and less time
                    if (cmpvalue != None and cmpvalue < 0):
                        dominance += 1                    

    # finally, return the number of dominances
    return dominance


# -----------------------------------------------------------------------------
# getrankingscore
#
# computes the total score of the specified domain for the given planner
# according to the row vector of total scores provided. 'name' is given only for
# compatibility with other get* handlers and it is unused here
# -----------------------------------------------------------------------------
def getrankingscore (name, idomain, iplanner, total):

    """
    computes the total score of the specified domain for the given planner
    according to the row vector of total scores provided. 'name' is given only
    for compatibility with other get* handlers and it is unused here
    """

    # just return the total score of iplanner in the specified domain
    return total[idomain][iplanner]


# -----------------------------------------------------------------------------
# updatebest
#
# updates the best value returned by VAL for a particular planners. It takes
# care of the special conditions of unsolved/invalid problems and updates best
# accordingly
# -----------------------------------------------------------------------------
def updatebest (best, idomain, iplanner, iproblem, values):

    """
    updates the value returned by VAL for particular domain/planner/problem. It
    takes special care of the unsolved/invalid problems and represent them
    accordingly
    """

    # accumulate the values of the matrix and store the results in the vector
    if (values [idomain][iplanner][iproblem] >= 0):

        # if no best value was known, update it with the first score
        if (best [idomain][iproblem] == UNSOLVED):
            best [idomain][iproblem] = values [idomain][iplanner][iproblem]

        # otherwise, take the minimum
        else:

            best [idomain][iproblem] = min (best [idomain][iproblem],
                                            values [idomain][iplanner][iproblem])


# -----------------------------------------------------------------------------
# updatebestqt
#
# updates the best number of pareto-dominances across a serie of values. Instead
# of taking the minimum as usual, we are interested here in taking the
# maximum. It takes care of the special conditions of unsolved/invalid problems
# and updates best accordingly
# -----------------------------------------------------------------------------
def updatebestqt (best, idomain, iplanner, iproblem, values):

    """
    updates the value returned by VAL for particular domain/planner/problem. It
    takes special care of the unsolved/invalid problems and represent them
    accordingly
    """

    # consider only positive values
    if (values [idomain][iplanner][iproblem] > 0):

        # if no best value was known, update it with the first value
        if (best [idomain][iproblem] == 0):
            best [idomain][iproblem] = values [idomain][iplanner][iproblem]
                        
        # otherwise, take the maximum
        else:

            best [idomain][iproblem] = max (best [idomain][iproblem],
                                            values [idomain][iplanner][iproblem])


# -----------------------------------------------------------------------------
# updatetotal
#
# updates the total score of each planner according to the given scores. It
# takes care of the special conditions of unsolved/invalid problems and updates
# best accordingly
# -----------------------------------------------------------------------------
def updatetotal (total, idomain, iplanner, iproblem, score):

    """
    updates the total score of each planner according to the given scores. It
    takes care of the special conditions of unsolved/invalid problems and
    updates best accordingly
    """

    if (score [idomain][iplanner][iproblem] > 0):
        total [idomain][iplanner] += score [idomain][iplanner][iproblem]


# -----------------------------------------------------------------------------
# updaterankingplanner
#
# updates the total score of each planner
# -----------------------------------------------------------------------------
def updaterankingplanner (total, name, idomain, iplanner, score):

    """
    updates the total score of each planner
    """

    if (score [name][idomain][iplanner] > 0):
        total [name][iplanner] += score [name][idomain][iplanner]

# -----------------------------------------------------------------------------
# updaterankingdomain
#
# updates the total score of each domain
# -----------------------------------------------------------------------------
def updaterankingdomain (total, name, idomain, iplanner, score):

    """
    updates the total score of each planner
    """

    if (score [name][idomain][iplanner] > 0):
        total [name][idomain] += score [name][idomain][iplanner]

# -----------------------------------------------------------------------------
# cmplexicographical
#
# returns a positive, zero or negative number depending on whether the first
# argument is smaller than, equal to, or larger than the second argument
# -----------------------------------------------------------------------------
def cmplexicographical (first, second):

    """
    returns a positive, zero or negative number depending on whether the first
    argument is smaller than, equal to, or larger than the second argument
    """

    if (first == second):
        return 0
    return {False: +1, True: -1}[first < second]


# -----------------------------------------------------------------------------
# cmpvectorial
#
# returns a negative, zero or positive number depending on whether vector
# contains in the first position a value which is smaller than, equal to, or
# larger than the value of vector in the second position
# -----------------------------------------------------------------------------
def cmpvectorial (first, second, vector):

    """
    returns a positive, zero or negative number depending on whether the first
    argument is smaller than, equal to, or larger than the second argument
    """

    if (vector [first] == vector[second]):
        return 0
    return {False: -1, True: +1}[vector [first] < vector [second]]


# -----------------------------------------------------------------------------
# cmppareto
#
# returns a negative, zero or positive number depending on whether first pareto
# dominates second, are equal or is pareto-dominated. If none of these relations
# hold, it returns None
#
# WARNING - it is assumed that both first and second have the same length
# -----------------------------------------------------------------------------
def cmppareto (first, second, position=0):

    """
    returns a negative, zero or positive number depending on whether first
    pareto dominates second, are equal or is pareto-dominated. If none of these
    relations hold, it returns None

    WARNING - it is assumed that both first and second have the same length
    """

    # case base - scalars are being compared
    if (position == len (first) - 1):

        if (first [position] == second [position]):
            return 0
        else:
            return {False:+1, True:-1} [first[position] < second[position]]

    # general case - vectors are being compared

    # first, compare the rest of the vector
    partial = cmppareto (first, second, position+1)

    # now, check each case separately
    if (partial == -1 and first [position] < second [position]):
        return -1                       # by now, first is pareto-dominated by second

    if (partial == 0 and first [position] == second [position]):
        return 0                        # by now, they seem to be equal

    if (partial == +1 and first [position] > second [position]):
        return +1                       # in this case, second is pareto-dominated by first

    # in any other case, there is no pareto-dominance
    return None


# Main services: computing matrices and vectors
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# computematrix
#
# this function abstracts the computation of any table. It receives three lists
# of keys and one function (along with a tuple of additional arguments) for
# computing a particular value of the matrix. It returns the resulting matrix
#
# The keys are interpreted as follows: one matrix is computed per keyA where
# columns are represented by keyB and rows by keyC
# -----------------------------------------------------------------------------
def computematrix (keyA, keyB, keyC, fgetitem, argsXY=()):

    """
    this function abstracts the computation of any table. It receives three
    lists of keys and one function (along with a tuple of additional arguments)
    for computing a particular value of the matrix. It returns the resulting
    matrix

    The keys are interpreted as follows: one matrix is computed per keyA where
    columns are represented by keyB and rows by keyC
    """

    # initialize the dictionary which will hold the values of the matrix
    matrix = dict ()
    for iA in keyA:

        matrix [iA] = dict ()

        # now, go through all the keys in keyB (columns of the matrix) and compute
        # the contents of the matrix
        for iB in keyB:

            # initialize this entry
            matrix [iA][iB] = dict ()

            # and for all rows of the matrix
            for iC in keyC:

                # compute the particular value of the matrix at (iA, iB, iC)
                matrix [iA][iB][iC] = fgetitem (iA, iB, iC, *argsXY)

    # return the matrix
    return matrix


# -----------------------------------------------------------------------------
# computevector
#
# this function abstracts the computation of any vector whose components are
# accumulated horizontally. It receives three lists of keys and two functions
# (along with a tuple of additional arguments) for initializing and updating the
# vector. It returns the resulting vector
#
# The keys are interpreted as follows: one vector is computed per keyA whose
# components are taken from the rows of the matrix generated by the columns in
# keyB and the rows in keyC
# -----------------------------------------------------------------------------
def computevector (keyA, keyB, keyC, finit, fupdate, argsinit=(), argsupdate=()):

    """
    this function abstracts the computation of any vector. It receives three
    lists of keys and two functions (along with a tuple of additional arguments)
    for initializing and updating the vector. It returns the resulting vector

    The keys are interpreted as follows: one vector is computed per keyA whose
    components are taken from the rows of the matrix generated by the columns in
    keyB and the rows in keyC
    """

    # initialize the dictionary which will hold the values of the vector
    vector = dict ()
    for iA in keyA:

        # initialize the contents of this vector
        vector [iA] = finit (*argsinit)
            
        # now, go through all the keys in keyB (rows of the matrix) and compute
        # the contents of the vector
        for iB in keyB:

            # and for all columns of the matrix
            for iC in keyC:

                # compute the particular value of the vector at (iA, iC)
                fupdate (vector, iA, iB, iC, *argsupdate)

    # return both the matrix and the vector
    return vector


# -----------------------------------------------------------------------------
# admindata
#
# generates the corresponding data structure to the info stored at the given
# directory for the problems, domains and planners that meet the given regexp
# -----------------------------------------------------------------------------
def admindata (directory, summary, name, problem, domain, planner):

    """
    generates the corresponding data structure to the info stored at the given
    directory for the problems, domains and planners that meet the given regexp
    using the metric of quality
    """

    # give preference to a summary if any has been provided
    if (summary):

        run = IPCrun.IPCrun ()
        run.deserialize (summary)

        # and now filter its contents according to the given regexps
        run.filter ({IPCrun.TRK            : planner,
                     IPCrun.TRK_PLN        : domain,
                     IPCrun.TRK_PLN_DMN    : problem,
                     IPCrun.TRK_PLN_DMN_PRB: '.*'})

    # otherwise, process the specified directory
    else:

        # guess the corresponding depth of the specified directory and raise an
        # exception in case it is not of the suitable depth
        depth = report.guessdepth (directory)
        if (depth != IPCrun.TRK):

            raise ValueError, """ Fatal Error - The directory '%s'
                 does not seem to be the root directory of the results of a track-subtrack""" % directory

        # compute the corresponding IPCrun to the specified data
        run = report.processdepth (directory = directory, name = name, 
                                   variables = [], unroll = False, sorting = [], 
                                   regexps = [problem, domain, planner, '.*'], 
                                   level = depth, depth = depth)

    # now, get the planners, domains and problems meeting the specified regexps
    planners = filter (lambda x:re.match (planner, x),  run.children (IPCrun.TRK))
    domains  = filter (lambda x:re.match (domain, x),   run.children (IPCrun.TRK_PLN))
    problems = filter (lambda x:re.match (problem, x),  run.children (IPCrun.TRK_PLN_DMN))

    # since this run is known to be at the shallowest level, use any combination
    # of planner, domain and problem to retrieve the current track and subtrack
    track = run [(planners [0] + IPCrun.CHAR_SEP + domains [0] + IPCrun.CHAR_SEP + problems [0]), 
                 IPCrun.TRACK]
    subtrack = run [(planners [0] + IPCrun.CHAR_SEP + domains [0] + IPCrun.CHAR_SEP + problems [0]), 
                    IPCrun.SUBTRACK]

    # finally, return the information of the IPCrun used, the list of domains,
    # planners and problems meeting the given regexps and, finally, the current
    # track and subtrack to be used in the name of tables if requested
    return (run, planners, domains, problems, track, subtrack)


# -----------------------------------------------------------------------------
# qualitydata
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the quality metric in the interval [0,
# timebound].
# -----------------------------------------------------------------------------
def qualitydata (run, planners, domains, problems, timebound = sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the quality metric in the interval [0,
    timebound]. 
    """

    # compute the matrix of values and the best scores per problem
    values = computematrix (domains, planners, problems, getvalue, (run, timebound))
    best   = computevector (domains, planners, problems, \
                            initdata, updatebest, (problems, UNSOLVED), (values,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, getscore, (values, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (problems) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (values, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# time0data
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the time0 metric
# -----------------------------------------------------------------------------
def time0data (run, planners, domains, problems, timebound = sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the time0 metric
    """

    # compute the matrix of values and the best timings per problem
    timings = computematrix (domains, planners, problems, gettiming, (run, timebound))
    best    = computevector (domains, planners, problems, \
                             initdata, updatebest, (problems, UNSOLVED), (timings,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, gettimescore0, (timings, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (problems) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (timings, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# time1data
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the time1 metric
# -----------------------------------------------------------------------------
def time1data (run, planners, domains, problems, timebound = sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the time1 metric
    """

    # compute the matrix of values and the best timings per problem
    timings = computematrix (domains, planners, problems, gettiming, (run, timebound))
    best    = computevector (domains, planners, problems, \
                             initdata, updatebest, (problems, UNSOLVED), (timings,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, gettimescore1, (timings, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (domains) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (timings, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# time2data
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the time2 metric
# -----------------------------------------------------------------------------
def time2data (run, planners, domains, problems, timebound = sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the time2 metric
    """

    # compute the matrix of values and the best timings per problem
    timings = computematrix (domains, planners, problems, gettiming, (run, timebound))
    best    = computevector (domains, planners, problems, \
                             initdata, updatebest, (problems, UNSOLVED), (timings,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, gettimescore2, (timings, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (problems) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (timings, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# solutionsdata
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the solutions metric
# -----------------------------------------------------------------------------
def solutionsdata (run, planners, domains, problems, timebound=sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the quality metric
    """

    # compute the matrix of values and the best scores per problem
    values = computematrix (domains, planners, problems, getsolution, (run, timebound))
    best   = computevector (domains, planners, problems, \
                            initdata, updatebest, (problems, UNSOLVED), (values,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, getscore, (values, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (problems) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (values, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# qtdata
#
# generates the matrices of values and scores along with the vectors of total
# and best scores according to the qt metric in the interval [0, timebound]. 
# -----------------------------------------------------------------------------
def qtdata (run, planners, domains, problems, timebound = sys.maxint):

    """
    generates the matrices of values and scores along with the vectors of total
    and best scores according to the qt metric in the interval [0, timebound].
    """

    # compute the matrix of tuples (q,t) per domain/planner/problem
    qt = computematrix (domains, planners, problems, getqt, (run, timebound))

    # In contraposition with the previous cases, the values are computed from
    # the tuples found so far. Thus, the values are defined as the number of
    # times that one particular entry pareto-dominates the same problem acroos
    # all planners in the same domain.

    # compute the matrix of values and the best scores per problem
    values = computematrix (domains, planners, problems, getparetodominance, (qt,planners,))
    best   = computevector (domains, planners, problems, \
                            initdata, updatebestqt, (problems, 0), (values,))

    # and compute also the matrix of scores and the total score per planner
    score = computematrix (domains, planners, problems, getscoreqt, (values, best))
    total = computevector (domains, planners, problems, \
                           initdata, updatetotal, (planners, 0), (score,))

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = initdata (domains, cmplexicographical)
    fcmpc = initdata (domains, cmplexicographical)
    fcmpargsr = initdata (domains, ())
    fcmpargsc = initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = initdata (domains, 'no.')
    upperright  = initdata (domains, 'best')
    bottomleft  = initdata (domains, 'total')
    bottomright = initdata (domains, '')

    # finally, return the list of domains, planners and problems meeting the
    # given regexps. Also, return the matrices of values and scores and the
    # column vector best and the row vector total, along with the sorting
    # criteria for rows (problems) and columns (planners). Besides, return the
    # current track and subtrack to be used in the name of tables if requested
    return (values, best, score, total, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# rankingdata
#
# generates the corresponding data structure to the ranking table with the
# global score of each planner per domain. Besides, it generates the total score
# per domain and the total score of each planner.
# -----------------------------------------------------------------------------
def rankingdata (planners, domains, values, score, total):

    """
    generates the corresponding data structure to the ranking table with the
    global score of each planner per domain. Besides, it generates the total
    score per domain and the total score of each planner.
    """

    # compute a unique matrix (named 'ranking') of values per planner and domain
    rkvalues  = computematrix (['ranking'], domains, planners, getrankingscore, (total,))

    # compute also the matrix of scores and the total score of every planner and domain
    rkscore   = computematrix (['ranking'], domains, planners, getrankingscore, (total,))
    rkplanner = computevector (['ranking'], domains, planners, \
                               initdata, updaterankingplanner, (planners, 0), (rkscore,))
    rkdomain  = computevector (['ranking'], domains, planners, \
                               initdata, updaterankingdomain, (domains, 0), (rkscore,))

    # explicitly specify sorting criteria, both for domains and planners
    fcmpr     = initdata (['ranking'], cmpvectorial)
    fcmpc     = initdata (['ranking'], cmpvectorial)
    fcmpargsr = initdata (['ranking'], (rkplanner ['ranking'],))
    fcmpargsc = initdata (['ranking'], (rkdomain ['ranking'],))

    # besides, create the headers and footers at the corners of this table
    upperleft   = initdata (['ranking'], 'planner')
    upperright  = initdata (['ranking'], 'total')
    bottomleft  = initdata (['ranking'], 'total')
    bottomright = initdata (['ranking'], '')

    # finally, return the values computed so far
    return (rkvalues, rkplanner, rkscore, rkdomain, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)



# Printing services
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# getname
#
# makes the substitution of all the placeholders in name. For this purpose, it
# receives the current values of track, subtrack, domain and time
# -----------------------------------------------------------------------------
def getname (name, track, subtrack, domain, time):

    """
    makes the substitution of all the placeholders in name. For this purpose, it
    receives the current values of track, subtrack, domain and time
    """

    # check the special case of time ---if it equals the largest integer, then
    # make it equal to infty
    if (time==sys.maxint):
        time='infty'

    # just make the proper substitutions
    return Template (name).substitute (track=track, subtrack=subtrack, domain=domain, 
                                       date=datetime.datetime.now ().strftime ("%c"),
                                       time=time)


# -----------------------------------------------------------------------------
# _prettytable
#
# prints a table whose contents are given in matrix. This is the matrix for the
# particular domain specified in the arguments. The matrix is arranged as a
# dictionary whose keys are the columns and point to other dictionaries whose
# values are the items to print per row. Besides, this service prints out two
# accumulated vectors (a column vector, cvector and a row vector, rvector).
#
# The column is entitled with the given name (which can contain a number of
# placeholders including track, subtrack and domain). Besides, the optional
# params [upper|bottom] [left|right] serve to specify strings to be printed at
# those locations in the rendered table
#
# Finally, the format is used to distinguish between ascii and html output
# -----------------------------------------------------------------------------
def _prettytable (icase, matrix, time, cvector, rvector, name, track, subtrack, format='table', 
                  fcmpr=cmplexicographical, fcmpc=cmplexicographical, fcmpargsr=(), fcmpargsc=(),
                  upperleft='', upperright='', bottomleft='', bottomright=''):

    """
    prints a table whose contents are given in matrix. This is the matrix for
    the particular domain specified in the arguments. The matrix is arranged as
    a dictionary whose keys are the columns and point to other dictionaries
    whose values are the items to print per row. Besides, this service prints
    out two accumulated vectors (a column vector, cvector and a row vector,
    rvector).
    
    The column is entitled with the given name (which can contain a number of
    placeholders including track, subtrack and domain). Besides, the optional
    params [upper|bottom] [left|right] serve to specify strings to be printed at
    those locations in the rendered table
    
    Finally, the format is used to distinguish between ascii and html output
    """

    def __translate (value):
        if (value >= 0):
            return ["%.2f" % value]
        elif (value == UNSOLVED):
            return ['---']
        elif (value == INVALID):
            return [' X ']
        else:
            raise ValueError, """
 Fatal Error - an illegal value has been found in _prettytable.__translate
""" % value


    # get the rows of keys of this table in the right order
    rowkeys = sorted (matrix[matrix.keys ()[0]].keys (), cmp=lambda x,y:fcmpr(x,y,*fcmpargsr))
    colkeys = sorted (matrix.keys (), cmp=lambda x,y:fcmpc (x,y,*fcmpargsc))

    # define tags according to the current format
    newline={False:"<br>", True: '\n'}[format=='table']
    boldopen={False:"<b>", True: ''}[format=='table']
    boldclose={False:"</b>", True: ''}[format=='table']
    emphasizeopen={False:"<em>", True: ''}[format=='table']
    emphasizeclose={False:"</em>", True: ''}[format=='table']

    # show the name of this table
    output = '\n' + getname (name, track, subtrack, icase, time) + '\n'

    # create the header of this matrix
    headers = [iheader for iheader in colkeys]
    headers.insert (0, upperleft)
    headers.append (upperright)

    # create the pretty table
    table = PrettyTable.PrettyTable (headers)

    # and now add the data for each row
    for irow in rowkeys:

        # start by inserting the name of this row
        row = [irow]

        # now the score of each pair (irow, icolumn)
        for icolumn in colkeys:

            row += __translate (matrix [icolumn][irow])

        # and now insert the corresponding value of the column vector
        row += __translate (cvector [irow])

        # and add it to the table
        table.add_row (row)

    # finally, add the accumulated row vector at the bottom
    row = [bottomleft]
    row += ["%.2f" % rvector [icolumn] for icolumn in colkeys]
    row.append (bottomright)
    table.add_row (row)

    # get the corresponding string
    if (format == 'table'):
        output += table.get_string ()
    else:
        output += table.get_html_string ()

    # show the legend
    output += "%s%s" % (newline, newline)
    output += " ---: unsolved%s" % newline
    output += "  X : invalid%s%s" % (newline, newline)
    output += " %screated by IPCrun %s (%s), %s%s%s%s" % (emphasizeopen,
                                                          IPCrun.__version__, IPCrun.__revision__ [1:-2],
                                                          datetime.datetime.now ().strftime ("%c"),
                                                          emphasizeclose, newline, newline)

    # and return the table in the specified format
    return output


# -----------------------------------------------------------------------------
# _wikitable
#
# prints a table whose contents are given in matrix. This is the matrix for the
# particular domain specified in the arguments. The matrix is arranged as a
# dictionary whose keys are the columns and point to other dictionaries whose
# values are the items to print per row. Besides, this service prints out two
# accumulated vectors (a column vector, cvector and a row vector, rvector).
#
# The column is entitled with the given name (which can contain a number of
# placeholders including track, subtrack and domain). Besides, the optional
# params [upper|bottom] [left|right] serve to specify strings to be printed at
# those locations in the rendered table
# -----------------------------------------------------------------------------
def _wikitable (icase, matrix, time, cvector, rvector, name, track, subtrack, format='wiki', 
                fcmpr=cmplexicographical, fcmpc=cmplexicographical, fcmpargsr=(), fcmpargsc=(),
                upperleft='', upperright='', bottomleft='', bottomright=''):

    """
    prints a table whose contents are given in matrix. This is the matrix for
    the particular domain specified in the arguments. The matrix is arranged as
    a dictionary whose keys are the columns and point to other dictionaries
    whose values are the items to print per row. Besides, this service prints
    out two accumulated vectors (a column vector, cvector and a row vector,
    rvector).
    
    The column is entitled with the given name (which can contain a number of
    placeholders including track, subtrack and domain). Besides, the optional
    params [upper|bottom] [left|right] serve to specify strings to be printed at
    those locations in the rendered table
    """

    def __translate (value):
        if (value >= 0):
            return "%.2f" % value
        elif (value == UNSOLVED):
            return " /!\ "
        elif (value == INVALID):
            return " {X} "
        else:
            raise ValueError, """
 Fatal Error - an illegal value has been found in _wikitable.__translate
"""


    # get the rows of keys of this table in the right order
    rowkeys = sorted (matrix[matrix.keys ()[0]].keys (), cmp=lambda x,y:fcmpr(x,y,*fcmpargsr))
    colkeys = sorted (matrix.keys (), cmp=lambda x,y:fcmpc (x,y,*fcmpargsc))

    # intialization
    output = "=== " + getname (name, track, subtrack, icase, time) + " ===\n"

    # create the header
    output += "|| '''" + upperleft + "''' || " + reduce (lambda x,y: str (x) + " || " + str (y),
                                  ["'''" + icol + "'''" for icol in colkeys])
    output +=  "|| '''" + upperright + "''' ||\n"

    # and now fill in the table
    for irow in rowkeys:

        # start by inserting the row identifier
        output += '|| ' + str (irow) + ' ||'

        # now the item at position (irow, icolumn)
        for icolumn in colkeys:

            output += ' ' + __translate (matrix [icolumn][irow]) + " ||"

        # and now the corresponding value of the column vector
        output += " '''" + __translate (cvector [irow]) + "''' ||\n"

    # finally, add the total score of every planner
    output += "|| '''" + bottomleft + "''' || "
    for icolumn in colkeys:
        output += "'''%.2f''' || " % rvector [icolumn]
    output += "'''" + bottomright + "''' ||\n"

    # show the footer
    output += "\n  /!\\ : unsolved"
    output += "\n  {X} : invalid"
    output += "\n''created by IPCrun %s (%s), %s''\n\n" % (IPCrun.__version__, 
                                                           IPCrun.__revision__ [1:-2],
                                                           datetime.datetime.now ().strftime ("%c"))

    # and return the string
    return output


# -----------------------------------------------------------------------------
# _latextable
#
# prints a table whose contents are given in matrix. This is the matrix for the
# particular domain specified in the arguments. The matrix is arranged as a
# dictionary whose keys are the columns and point to other dictionaries whose
# values are the items to print per row. Besides, this service prints out two
# accumulated vectors (a column vector, cvector and a row vector, rvector).
#
# The column is entitled with the given name (which can contain a number of
# placeholders including track, subtrack and domain). Besides, the optional
# params [upper|bottom] [left|right] serve to specify strings to be printed at
# those locations in the rendered table
# -----------------------------------------------------------------------------
def _latextable (icase, matrix, time, cvector, rvector, name, track, subtrack, format='latex', 
                 fcmpr=cmplexicographical, fcmpc=cmplexicographical, fcmpargsr=(), fcmpargsc=(),
                 upperleft='', upperright='', bottomleft='', bottomright=''):

    """
    prints a table whose contents are given in matrix. This is the matrix for
    the particular domain specified in the arguments. The matrix is arranged as
    a dictionary whose keys are the columns and point to other dictionaries
    whose values are the items to print per row. Besides, this service prints
    out two accumulated vectors (a column vector, cvector and a row vector,
    rvector).
    
    The column is entitled with the given name (which can contain a number of
    placeholders including track, subtrack and domain). Besides, the optional
    params [upper|bottom] [left|right] serve to specify strings to be printed at
    those locations in the rendered table
    """

    def __translate (value):
        if (value >= 0):
            return "%.2f" % value
        elif (value == UNSOLVED):
            return "$\\varnothing$"
        elif (value == INVALID):
            return "\\ding{56}"
        else:
            raise ValueError, """
 Fatal Error - an illegal value has been found in _latextable.__translate
"""


    # get the rows of keys of this table in the right order
    rowkeys = sorted (matrix[matrix.keys ()[0]].keys (), cmp=lambda x,y:fcmpr(x,y,*fcmpargsr))
    colkeys = sorted (matrix.keys (), cmp=lambda x,y:fcmpc (x,y,*fcmpargsc))

    # intialization
    output = """
\\section*{%s}
\\begin{table}[h!]
  \\centering
  \\begin{tabular}""" % getname (name, track, subtrack, icase, time)

    # create the header

    # first the formatting line
    output += "{|l|"
    for icolumn in matrix.keys ():
        output += "c@{\\hspace{2pt}}"

    output += "|c|} \\hline\n"

    # now, the names of the keys in the columns
    output += "\\textbf{" + upperleft + "} & "
    for icolumn in colkeys:
        output += "\\textbf{" + icolumn + "} & "

    output += "\\textbf{" + upperright + "} \\\\ \\hline\\hline\n"

    # and now fill in the table
    for irow in rowkeys:

        # start by inserting the row identifier
        output += "\\textbf{" + irow + "} & "

        # now the item at position (irow, icolumn)
        for icolumn in colkeys:

            output += __translate (matrix [icolumn][irow]) + " & "

        # and now the corresponding value of the column vector
        output += "\\textbf{" + __translate (cvector [irow]) + "}\\\\%s\n" % {False:'', True:"\\hline"}[irow==sorted (matrix[matrix.keys ()[0]].keys (), cmp=lambda x,y:fcmpr(x,y,*fcmpargsr))[-1]]

    # finally, add the total score of every planner
    output += "\\textbf{" + bottomleft + "} & "
    for icolumn in colkeys:
        output += "\\textbf{%.2f} & " % rvector [icolumn]
    output += "\\textbf{" + bottomright + "} \\\\ \\hline\n"

    # end the environment
    output += """  \\end{tabular}
  \\label{fig:%s}
\\end{table}\n
\\vfil\n\n""" % (getname ("$track-$subtrack-$domain", track, subtrack, icase, time))

    # now, print a matrix of squared boxes with different colors that represent
    # the same scores shown up there
    output +="\\begin{pspicture}(0,0)(%i,%i)\n" % \
        (10 * len (matrix.keys ()),
         10 * len (matrix [matrix.keys ()[0]].keys ()))

    # create a matrix of colors for all rows and columns:
    for irow in range (0, len (rowkeys)):
        for icol in range (0, len (colkeys)):
            if (matrix [colkeys[icol]][rowkeys[irow]] >= 0):
                output += "   \psframe[linewidth=0.1pt,fillstyle=solid,fillcolor=%s-%s-%s](%i,%i)(%i,%i)\n" % \
                    (icase, colkeys [icol], rowkeys [irow], 10*icol + 1, 10*(len(rowkeys)-irow) + 1, 10*(1+icol) - 1, 10*(1+(len(rowkeys)-irow)) - 1)
            elif (matrix [colkeys[icol]][rowkeys[irow]] == UNSOLVED):
                output += "   \psframe[linewidth=0.1pt,fillstyle=solid,fillcolor=yellow](%i,%i)(%i,%i)\n" % \
                    (10*icol + 1, 10*(len(rowkeys)-irow) + 1, 10*(1+icol) - 1, 10*(1+(len(rowkeys)-irow)) - 1)
            elif (matrix [colkeys[icol]][rowkeys[irow]] == INVALID):
                output += "   \psframe[linewidth=0.1pt,fillstyle=solid,fillcolor=red](%i,%i)(%i,%i)\n" % \
                    (10*icol + 1, 10*(len(rowkeys)-irow) + 1, 10*(1+icol) - 1, 10*(1+(len(rowkeys)-irow)) - 1)

    # and now show the labels
    for icol in range (0, len (colkeys)):
        output += "   \\rput(%i, %i){%s}\n" % (5+10*icol, 15+10*len (rowkeys), colkeys [icol])
        output += "   \\rput(%i, %i){%s}\n" % (5+10*icol, 5, colkeys [icol])

    for irow in range (0, len (rowkeys)):
        output += "   \\rput[r](%i, %i){%s}\n" % (-2, 5+10*(len (rowkeys)-irow), rowkeys [irow])
        output += "   \\rput[l](%i, %i){%s}\n" % (2+10*len (colkeys), 5+10*(len (rowkeys)-irow), rowkeys [irow])

    output += "\\end{pspicture}"

    # now, show the signature
    output += """\n
\\begin{flushleft}
  created by IPCrun %s (%s), %s\\\\
\\end{flushleft}
\\clearpage\n\n""" % (IPCrun.__version__, IPCrun.__revision__ [1:-2],
                      datetime.datetime.now ().strftime ("%c"))

    # and return the string
    return output


# -----------------------------------------------------------------------------
# _latexcolors
# 
# returns LaTeX code for defining all the colors that are necessary for plotting
# the scores in matrix
# -----------------------------------------------------------------------------
def _latexcolors (matrix):
    """
    returns LaTeX code for defining all the colors that are necessary for plotting
    the scores in matrix
    """

    # first, get the higher and lower values in each matrix
    lower = {}
    upper = {}

    # for all keys in matrix
    for ikeyA in matrix.keys ():

        # for all columns in this matrix
        for ikeyB in matrix [ikeyA].keys ():

            # and rows
            for ikeyC in matrix[ikeyA][ikeyB].keys ():

                # only in case we have a non-negative value at this position,
                # compute the upper and lower
                if (matrix [ikeyA][ikeyB][ikeyC] >= 0):

                    # if both lower and upper are empty, the init them
                    if (ikeyA not in lower or ikeyA not in upper):
                        lower [ikeyA] = matrix [ikeyA][ikeyB][ikeyC]
                        upper [ikeyA] = matrix [ikeyA][ikeyB][ikeyC]

                    # otherwise, perform the comparison
                    else:

                        lower [ikeyA] = min (lower [ikeyA], matrix [ikeyA][ikeyB][ikeyC])
                        upper [ikeyA] = max (upper [ikeyA], matrix [ikeyA][ikeyB][ikeyC])

    # now, compute each particular color

    # Initialization
    code = ''

    # for all keys in matrix
    for ikeyA in matrix.keys ():

        # for all columns in this matrix
        for ikeyB in matrix[ikeyA].keys ():

            # and rows
            for ikeyC in matrix[ikeyA][ikeyB].keys ():

                # only in case we have a non-negative value at this position,
                # compute the corresponding color
                if (matrix [ikeyA][ikeyB][ikeyC] >= 0):

                    # compute the gray scale of this score
                    if (upper [ikeyA] != lower [ikeyA]):
                        color = 1 - (matrix [ikeyA][ikeyB][ikeyC] - lower [ikeyA]) / \
                            (upper [ikeyA] - lower [ikeyA])
                    else:
                        color = 0

                    code += "\\definecolor{%s-%s-%s}{rgb}{%0.2f,%0.2f,%0.2f}\n" \
                        % (ikeyA, ikeyB, ikeyC, color, color, color)
    
    # return the colors computed so far
    return code


# -----------------------------------------------------------------------------
# _latexdoc
# 
# creates a LaTeX document inserting the preamble and ending of the tex
# document. In the middle it inserts the latex code in 'tables' and other
# figures using the given colors (in LaTeX code)
# -----------------------------------------------------------------------------
def _latexdoc (file, colors, tables):

    """
    creates a LaTeX document inserting the preamble and ending of the tex
    document. In the middle it inserts the latex code in 'tables' and other
    figures using the given colors (in LaTeX code)
    """

    # create the requested file for writting
    stream = open (file, 'w')
    
    # write the preamble
    stream.write("""
\\documentclass{article}
\\usepackage[a4paper,landscape,margin=0.5cm]{geometry}
\\usepackage{supertabular}
\\usepackage{scrtime}
\\usepackage{amssymb}
\\usepackage{pifont}
\\usepackage{pst-all}
\\psset{xunit=5pt}
\\psset{yunit=1pt}
\\begin{document}
%s
\\scriptsize
\\setlength{\\tabcolsep}{1pt}
\\centering""" % colors)

    # now, insert the tables
    stream.write (tables)
    
    # end the document
    stream.write ("\\end{document}")

    # and close the file
    stream.close()    

    # return a string signaling that the file was generated
    return (" File %s generated" % file)


# -----------------------------------------------------------------------------
# _octavetable
#
# prints a table whose contents are given in matrix. This is the matrix for the
# particular domain specified in the arguments. The matrix is arranged as a
# dictionary whose keys are the columns and point to other dictionaries whose
# values are the items to print per row. Besides, this service prints out two
# accumulated vectors (a column vector, cvector and a row vector, rvector).
#
# The column is entitled with the given name (which can contain a number of
# placeholders including track, subtrack and domain). Besides, the optional
# params [upper|bottom] [left|right] are only used here for compatibility with
# other print drivers ---unused here!
# -----------------------------------------------------------------------------
def _octavetable (icase, matrix, time, cvector, rvector, name, track, subtrack, format='octave', 
                  fcmpr=cmplexicographical, fcmpc=cmplexicographical, fcmpargsr=(), fcmpargsc=(),
                  upperleft='', upperright='', bottomleft='', bottomright=''):

    """
    prints a table whose contents are given in matrix. This is the matrix for
    the particular domain specified in the arguments. The matrix is arranged as
    a dictionary whose keys are the columns and point to other dictionaries
    whose values are the items to print per row. Besides, this service prints
    out two accumulated vectors (a column vector, cvector and a row vector,
    rvector).
    
    The column is entitled with the given name (which can contain a number of
    placeholders including track, subtrack and domain). Besides, the optional
    params [upper|bottom] [left|right] are only used here for compatibility with
    other print drivers ---unused here!
    """

    def __translate (value):
        if (value >= 0):
            return str (value)
        elif (value == UNSOLVED):
            return '-1'
        elif (value == INVALID):
            return '-2'
        else:
            raise ValueError, """
 Fatal Error - an illegal value has been found in _octavetable.__translate
"""


    # get the rows of keys of this table in the right order
    rowkeys = sorted (matrix[matrix.keys ()[0]].keys (), cmp=lambda x,y:fcmpr(x,y,*fcmpargsr))
    colkeys = sorted (matrix.keys (), cmp=lambda x,y:fcmpc (x,y,*fcmpargsc))

    # intialization
    output = "# created by IPCrun %s (%s), %s\n" % (IPCrun.__version__, IPCrun.__revision__ [1:-2],
                                                    datetime.datetime.now ().strftime ("%c"))
    output += "# " + getname (name, track, subtrack, icase, time) + '\n'
    output += "# name: best_%s\n" % icase
    output += "# type: matrix\n"
    output += "# rows: %i\n" % len (matrix[matrix.keys ()[0]].keys ())
    output += "# columns: 2\n"
    
    # generate the matrix with the column vector
    for irow in rowkeys:
        output += str(irow) + ' ' + __translate (cvector [irow]) + '\n'

    # now show the bidimensional matrix
    output += '\n'
    output += "# name: scores_%s\n" % icase
    output += "# type: matrix\n"
    output += "# rows: %i\n" % len (matrix[matrix.keys ()[0]].keys ())
    output += "# columns: %i\n" % (1 + len (matrix.keys ()))

    for irow in rowkeys:

        # start by inserting the row identifier
        output += str (irow)

        # now the score of each pair (problem, planner)
        for icolumn in colkeys:

            output += ' ' + __translate (matrix [icolumn][irow])

        # and now show the newline character
        output += '\n'

    # the row vector is skipped because this is usually indexed by the keys used
    # in the columns which are the planners names. Unfortunately, Octave does
    # not provide an easy mechanism to load matrices that can be made up of
    # either numbers of strings. And this is really awkward since planners are
    # identified by strings. Alternatives such as the dataframe of Octave do not
    # simplify things ---or that's what it seems to me
    output += '\n'

    # and return the string
    return output


# -----------------------------------------------------------------------------
# _exceltable
#
# prints a table whose contents are given in matrix. This is the matrix for the
# particular domain specified in the arguments. The matrix is arranged as a
# dictionary whose keys are the columns and point to other dictionaries whose
# values are the items to print per row. Besides, this service prints out two
# accumulated vectors (a column vector, cvector and a row vector, rvector).
#
# The column is entitled with the given name (which can contain a number of
# placeholders including track, subtrack and domain). Besides, the optional
# params [upper|bottom] [left|right] serve to specify strings to be printed at
# those locations in the rendered table
# -----------------------------------------------------------------------------
def _exceltable (cases, matrix, time, cvector, rvector, name, track, subtrack, format, 
                 fcmpr, fcmpc, fcmpargsr, fcmpargsc,
                 upperleft='', upperright='', bottomleft='', bottomright=''):

    """
    prints a table whose contents are given in matrix. This is the matrix for
    the particular domain specified in the arguments. The matrix is arranged as
    a dictionary whose keys are the columns and point to other dictionaries
    whose values are the items to print per row. Besides, this service prints
    out two accumulated vectors (a column vector, cvector and a row vector,
    rvector).
    
    The column is entitled with the given name (which can contain a number of
    placeholders including track, subtrack and domain). Besides, the optional
    params [upper|bottom] [left|right] serve to specify strings to be printed at
    those locations in the rendered table
    """

    def __translate (value):
        if (value >= 0):
            return value
        elif (value == UNSOLVED):
            return "uns."
        elif (value == INVALID):
            return "inv."
        else:
            raise ValueError, """
 Fatal Error - an illegal value has been found in _octavetable.__translate
"""


    # create the excel page
    wb = pyExcelerator.Workbook ()

    # create the styles

    # for the header
    hstyle = pyExcelerator.XFStyle ()
    hstyle.font.name = "Arial"
    hstyle.font.bold = True

    # for unsolved entries
    ustyle = pyExcelerator.XFStyle ()
    ustyle.font.name = "Arial"
    ustyle.font.bold = True
    ustyle.font.colour_index = 0x10             # dark red

    # for invalid entries
    istyle = pyExcelerator.XFStyle ()
    istyle.font.name = "Arial"
    istyle.font.bold = True
    istyle.font.colour_index = 0x2              # light red

    # for the ordinary entries
    vstyle = pyExcelerator.XFStyle ()
    vstyle.font.name = "Arial"
    vstyle.font.bold = False
    vstyle.font.colour_index = 0x27              # dark blue

    filename = "matrix.xls"

    # for all the specified domains ---note that there is an important
    # difference with other formatters. The reason is that it seems that
    # pyExcelerator does not provide any means for opening an existing workbook
    # to add worksheets so that to have a number of them, they all have to be
    # created in a row
    for icase in cases:

        # get the rows of keys of this table in the right order
        colkeys = sorted (matrix [icase].keys (), cmp=lambda x,y:fcmpc [icase](x,y,*fcmpargsc [icase]))
        rowkeys = sorted (matrix [icase][colkeys[0]].keys (), cmp=lambda x,y:fcmpr [icase](x,y,*fcmpargsr [icase]))

        # initialization
        row=col=1        

        # create a worksheet with the name of the table 
        ws = wb.add_sheet ("%s" % getname (name, track, subtrack, icase, time))

        # create the panes splitters
        ws.panes_frozen = True
        ws.horz_split_pos = 2
        ws.vert_split_pos = 2

        # create the header
        ws.write (row, col, upperleft [icase], hstyle)
        col += 1
        for icolumn in colkeys:
            ws.write (row, col, icolumn, hstyle)
            col += 1
        ws.write (row, col, upperright [icase], hstyle)

        row += 1
        col = 1

        # and now fill in the matrix
        for irow in rowkeys:

            # start by showing the row identifier
            ws.write (row, col, irow, hstyle)
            col += 1

            # now the content of each pair (irow, icolumn)
            for icolumn in colkeys:

                if (matrix[icase][icolumn][irow] == UNSOLVED):
                    ws.write (row, col, "unsolved", ustyle)
                elif (matrix [icase] [icolumn][irow] == INVALID):
                    ws.write (row, col, "invalid", istyle)
                else:
                    ws.write (row, col, matrix [icase] [icolumn][irow], vstyle)
                col += 1

            # and now insert the best score for this planner
            if (cvector [icase] [irow] == UNSOLVED):
                ws.write (row, col, "unknown", hstyle)
            else:
                ws.write (row, col, cvector [icase] [irow], hstyle)
            row += 1
            col = 1

        # finally, add the total score of every planner
        ws.write (row, col, bottomleft [icase], hstyle)
        col += 1
        for icolumn in colkeys:
            ws.write (row, col, rvector [icase] [icolumn], hstyle)
            col += 1
        ws.write (row, col, bottomright [icase], hstyle)

        # show the footer
        row += 2
        col = 1
        ws.write (row, col, "created by IPCrun %s (%s), %s\n" % (IPCrun.__version__, 
                                                                 IPCrun.__revision__ [1:-2],
                                                                 datetime.datetime.now ().strftime ("%c")))

    # save the excel page
    wb.save (filename)

    return ("Excel file '%s' generated" % filename)


# -----------------------------------------------------------------------------
# tablestr
#
# print the matrices given per case, along with the column vector and the row
# vector specified in the requested format. The 'case' is only a list of keys
# which appear also in matrix so that there are as many matrices as
# cases. Besides, tables are given a name which can contain placeholders. These
# can be, among others, the track, subtrack and time. Finally, the fcmp* are cmp
# functions used for sorting rows (r) and columns (c). These functions can
# receive an arbitrary list of parameters in fcmpargs*.
#
# the parameters upperleft, upperright, bottomleft and bottomright stand for a
# dictionary that contains for each case (table) the strings to be shown at the
# four corners of each table
# -----------------------------------------------------------------------------
def tablestr (case, matrix, cvector, rvector, fcmpr, fcmpc, 
              fcmpargsr, fcmpargsc, upperleft, 
              upperright, bottomleft, bottomright, 
              name, track, subtrack, time, format):

    """
    print the matrices given per case, along with the column vector and the row
    vector specified in the requested format. The 'case' is only a list of keys
    which appear also in matrix so that there are as many matrices as
    cases. Besides, tables are given a name which can contain
    placeholders. These can be, among others, the track, subtrack and
    time. Finally, the fcmp* are cmp functions used for sorting rows (r) and
    columns (c). These functions can receive an arbitrary list of parameters in
    fcmpargs*.
    
    the parameters upperleft, upperright, bottomleft and bottomright stand for a
    dictionary that contains for each case (table) the strings to be shown at
    the four corners of each table
    """

    # get the corresponding formatter
    formatter = {'table' : _prettytable,
                 'wiki'  : _wikitable,
                 'html'  : _prettytable,
                 'octave': _octavetable,
                 'excel' : _exceltable,
                 'latex' : _latextable}[format]

    # and now call the right formatter, once per case if format ain't excel
    strout = ''
    if (format != 'excel'):
        for icase in case:
            strout += formatter (icase, matrix [icase], time, cvector [icase], rvector [icase], 
                                 name, track, subtrack, format, 
                                 fcmpr[icase], fcmpc[icase], fcmpargsr[icase], fcmpargsc[icase],
                                 upperleft [icase], upperright [icase], bottomleft [icase], bottomright [icase])

    # otherwise, let the formatter for excel pages to draw information on all
    # tables at the same time ---the reason is that as far as it seems, the
    # pyExcelerator package does not allow to open and extend an existing
    # workbook with new worksheets so that if the excel formatter is invoked
    # consecutively, the same file is replaced over and over again
    else:
        strout += formatter (case, matrix, time, cvector, rvector,
                             name, track, subtrack, format, 
                             fcmpr=fcmpr, fcmpc=fcmpc, 
                             fcmpargsr=fcmpargsr, fcmpargsc=fcmpargsc,
                             upperleft=upperleft, upperright=upperright, 
                             bottomleft=bottomleft, bottomright=bottomright)

    # in case the latex format has been required, create the whole LaTeX
    # document with its preamble and ending
    if (format == 'latex'):

        # first compute all colors necessary for making nice drawings of the
        # results
        colors = _latexcolors (matrix)
        strout = _latexdoc ('matrix.tex', colors, strout)

    # and finally return the whole string
    return strout


# -----------------------------------------------------------------------------
# dispatcher
#
# this class creates a dispatcher for automating the creation of score tables
# -----------------------------------------------------------------------------
class dispatcher (object):
    """
    this class creates a dispatcher for automating the creation of score tables
    """

    # Default constructor
    def __init__ (self, directory, summary, metric, name, planner, 
                  domain, problem, time, style, wxprogressdialog=None):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._directory, self._summary, self._metric, self._name, self._planner, 
         self._domain, self._problem, self._time, self._style, wxprogressdialog) = \
         (directory, summary, metric, name, planner, 
          domain, problem, time, style, wxprogressdialog)


    # Execute the following body when creating reports
    def __enter__ (self):
        """
        Execute the following body when creating the score tables
        """

        # before proceeding, check that all parameters are correct
        checkflags (self._directory, self._summary)


    # The following method sets up the environment for automating the creation
    # of score tables
    def score (self):
        """
        The following method sets up the environment for automating the creation
        of score tables
        """
        
        # generate the corresponding structure that contains all the information
        # from the given directory/summary
        (self._run, self._planners, self._domains, self._problems, self._track, self._subtrack) = \
            admindata (self._directory, self._summary, self._name, 
                       self._problem, self._domain, self._planner)

        if (self._metric == 'quality'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             qualitydata (self._run, self._planners, self._domains, self._problems, self._time)
        elif (self._metric == 'qt'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             qtdata (self._run, self._planners, self._domains, self._problems, self._time)
        elif (self._metric == 'time0'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             time0data (self._run, self._planners, self._domains, self._problems, self._time)
        elif (self._metric == 'time1'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             time1data (self._run, self._planners, self._domains, self._problems, self._time)
        elif (self._metric == 'time2'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             time2data (self._run, self._planners, self._domains, self._problems, self._time)
        elif (self._metric == 'solutions'):
            (self._values, self._best, self._score, self._total, 
             self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
             self._upperleft, self._upperright, self._bottomleft, self._bottomright) = \
             solutionsdata (self._run, self._planners, self._domains, self._problems, self._time)
        else:
            print """
     Unrecognized metric '%s'
     """ % self._metric
            sys.exit ()

        # now, in case that more than one domain has been requested
        if (len (self._domains) > 1):

            # besides, create the raking table with the information of all planners
            # and domains
            (self._rkvalues, self._rkbest, self._rkscore, self._rktotal, 
             self._rkfcmpr, self._rkfcmpc, self._rkfcmpargsr, self._rkfcmpargsc,
             self._rkupperleft, self._rkupperright, self._rkbottomleft, self._rkbottomright) = \
             rankingdata (self._planners, self._domains, self._values, self._score, self._total)

            self._domains += ['ranking']
            (self._score ['ranking'], self._best ['ranking'], self._total ['ranking'], 
             self._fcmpr ['ranking'], self._fcmpc ['ranking'], 
             self._fcmpargsr ['ranking'], self._fcmpargsc ['ranking'],
             self._upperleft ['ranking'], self._upperright ['ranking'], 
             self._bottomleft ['ranking'], self._bottomright ['ranking']) = \
             (self._rkscore ['ranking'], self._rkbest ['ranking'], self._rktotal ['ranking'],
              self._rkfcmpr ['ranking'], self._rkfcmpc ['ranking'],  
              self._rkfcmpargsr ['ranking'], self._rkfcmpargsc ['ranking'],
              self._rkupperleft ['ranking'], self._rkupperright ['ranking'], 
              self._rkbottomleft ['ranking'], self._rkbottomright ['ranking'])

        # now, depending on the style, it prints out data in the specified format
        print tablestr (self._domains, self._score, self._best, self._total, 
                        self._fcmpr, self._fcmpc, self._fcmpargsr, self._fcmpargsc,
                        self._upperleft, self._upperright, self._bottomleft, self._bottomright, 
                        self._name, self._track, self._subtrack, self._time, self._style)


            
    # clean-up
    def __exit__ (self, type, value, traceback):
        """
        Clean-up
        """

        pass


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    PROGRAM_NAME = sys.argv[0]              # get the program name

    # parse the arguments
    PARSER = create_parser ()
    ARGS = PARSER.parse_args ()

    # show the current version and also a comprehensive view of the current switches
    if (not ARGS.quiet):
        version ()
        show_switches (ARGS.directory, ARGS.summary, ARGS.metric, ARGS.name,
                       ARGS.planner, ARGS.domain, ARGS.problem, ARGS.time, ARGS.style)

    # Now, enclose all the process in a with statement
    DISPATCHER = dispatcher (ARGS.directory, ARGS.summary, ARGS.metric, ARGS.name,
                             ARGS.planner, ARGS.domain, ARGS.problem, ARGS.time, ARGS.style)
    with DISPATCHER:
        
        # and request the generation of the report
        DISPATCHER.score ()



# Local Variables:
# mode:python
# fill-column:80
# End:
