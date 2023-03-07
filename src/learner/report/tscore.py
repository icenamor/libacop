#!/usr/bin/env python
#
# score.py
# Description: computes how the score evolves over time
# -----------------------------------------------------------------------------
#
# Started on  <Thu May 19 17:32:33 2011 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:10:27 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: score.py 283 2011-07-05 10:18:09Z clinares                           $
# $Date:: 2011-07-05 12:18:09 +0200 (Tue, 05 Jul 2011)                       $
# $Revision:: 283                                                            $
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
computes how the score evolves over time
"""

__version__  = '1.3'
__revision__ = '$Revision: 283 $'
__date__     = '$Date: 2011-07-05 12:18:09 +0200 (Tue, 05 Jul 2011) $'

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
import score            # IPC score services

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
    filtering.add_argument ('-l', '--labels',
                            default=sys.maxint,
                            type=int,
                            help='if given, approximately these number of time stamps is picked up among those in the interval defined by --time')
        
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
                             choices=['table','octave','html','excel','wiki'],
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
def show_switches (directory, summary, metric, name, planner, domain, problem, 
                   timebound, timelabels, style):

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
 * timebound      : %s (%s points)
 * style          : %s
 -----------------------------------------------------------------------------\n""" % ({False:'summary', True:'directory'}[bool (directory)], {False:summary, True:directory}[bool (directory)], metric, name, planner, domain, problem, {False:'infty', True:str(timebound)}[timebound < sys.maxint], {False: 'all', True: str (timelabels)}[timelabels < sys.maxint],style))


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


# -----------------------------------------------------------------------------
# gettimings
#
# get the time stamps from 'run' when a planner (among those specified) produced
# a valid solution for any of the selected problems in the given domains. It
# returns a dictionary with the timings properly sorted in ascending order per
# domain. If timelabels is given, approximately these number of time stamps is
# returned.
# -----------------------------------------------------------------------------
def gettimings (run, planners, domains, problems, timebound = sys.maxint, timelabels = sys.maxint):

    """
    get the time stamps from 'run' when a planner (among those specified)
    produced a valid solution for any of the selected problems in the given
    domains. It returns a dictionary with the timings properly sorted in
    ascending order per domain. If timelabels is given, approximately these
    number of time stamps is returned.
    """

    # initialization
    timings = dict ()

    # go through all the combinations of planners/domains/problems and retrieve
    # the timings when each planner produced a valid solution (according to VAL)
    for idomain in domains:

        timings [idomain] = list ()

        for iplanner in planners:

            for iproblem in problems:

                # compute the key to access 'run'
                key = iplanner + IPCrun.CHAR_SEP + idomain + IPCrun.CHAR_SEP + iproblem

                # retrieve the timings for this particular
                # planner/domain/problem and add them to this entry removing
                # duplicates and sorting all the timings in ascending order
                timings [idomain] = sorted (list (set (timings [idomain] + 
                                                       [itime
                                                        for itime in run[(key, IPCrun.OKTIMESOLS)]
                                                        if itime <= timebound])))

        # now, in case that a specific number of time stamps has been required,
        # take those equidistributed from the current list of time labels
        if (timelabels < sys.maxint):

            timings [idomain] = [timing for idx,timing in enumerate (timings [idomain])
                                 if (idx % math.ceil (float (len (timings [idomain])) / timelabels) == 0)]        

    # now, compute the timings for the ranking table even if only one domain has
    # been specified. These timings result from merging all timings for all
    # domains
    timings ['ranking'] = list ()
    for idomain in domains:
        timings ['ranking'] = list (set (timings ['ranking'] + timings [idomain]))
                
    # return the dictionary computed so far
    return timings


# -----------------------------------------------------------------------------
# computeserie
#
# this function uses the data in run to compute how the score (computed with
# fcomp) of the selected planners evolves over time when solving the specified
# problems in all the given domains at each timelabel
# -----------------------------------------------------------------------------
def computeserie (run, planners, domains, problems, fcomp, timelabels):

    """
    this function uses the data in run to compute how the score (computed with
    fcomp) of the selected planners evolves over time when solving the specified
    problems in all the given domains at each timelabel
    """

    # initialization
    matrix = dict ()
    best   = dict ()
    last   = dict ()

    # for every domain
    for idomain in domains:

        matrix [idomain] = dict ()
        last   [idomain] = dict ()

        # for every time step
        for itimelabel in timelabels [idomain]:

            # compute the score of this planners for all problems in this domain
            # in the interval [0, itimelabel] and retrieve the total score for
            # all planners
            tscore = fcomp (run, planners, [idomain], problems, itimelabel) [3]

            # now, copy the total scores to the right places in this dictionary
            for iplanner in planners:

                if (iplanner not in matrix [idomain].keys ()):
                    matrix [idomain][iplanner] = dict ()
                matrix [idomain][iplanner][itimelabel] = tscore [idomain][iplanner]

                # compute now the corresponding value of the row vector (last)
                last [idomain][iplanner] = matrix[idomain][iplanner][max (matrix[idomain][iplanner].keys ())]

    # compute now the column vector with the best and total scores - a caveat
    # here: since score.computevector initializes a vector (according to
    # score.initdata) and recreates its contents (according to
    # score.updatebestqt) everytime it is invoked, the returned value has to be
    # stored in different places ---that is why, a separate dict 'best' is
    # maintained here. On the other hand, score.computevector is programmed to
    # be able to compute the vectors for a wide of domains so that it returns
    # the vectors in a dictionary for domains ---that is why the 'idomain' is
    # accessed separately in every invokation.
    for idomain in domains:
        best [idomain] = score.computevector ([idomain], planners, timelabels [idomain], \
                                              score.initdata, score.updatebestqt, \
                                              (timelabels [idomain], 0), (matrix,)) [idomain]

    # also create specific sorting criteria: just lexicographically for both
    # domains and planners. These functions have no arguments, so signal this
    # explicitly
    fcmpr = score.initdata (domains, score.cmplexicographical)
    fcmpc = score.initdata (domains, score.cmplexicographical)
    fcmpargsr = score.initdata (domains, ())
    fcmpargsc = score.initdata (domains, ())

    # besides, create the headers and footers at the corners of these tables
    upperleft   = score.initdata (domains, 'time')
    upperright  = score.initdata (domains, 'best')
    bottomleft  = score.initdata (domains, 'last')
    bottomright = score.initdata (domains, '')

    # finally, return the matrix of scores and the column vector best and the
    # row vector last, along with the sorting criteria for rows (time stamps)
    # and columns (planners)
    return (matrix, best, last, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


# -----------------------------------------------------------------------------
# computeranking
#
# this function just goes through the scores in all the specified
# domains/planners and computes the overall score (i.e., the ranking) at the
# specified timings
# -----------------------------------------------------------------------------
def computeranking (planners, domains, scores, timelabels):
    """
    this function just goes through the scores in all the specified
    domains/planners and computes the overall score (i.e., the ranking) at the
    specified timings
    """

    def __score (score, timing=sys.maxint):
        """
        computes the score at the specified timing
        """

        # compute the time labels that fall in the interval [0, timing]
        interval = [itime for itime in score.keys () if itime <= timing]

        # if the above sequence is empty return 0, otherwise, return the score
        # of the latest timing
        if (interval):
            return score [max (interval)]
        return 0
        

    # initialization
    matrix = dict ()
    best   = dict ()
    last   = dict ()

    matrix ['ranking'] = dict ()
    best   ['ranking'] = dict ()
    last   ['ranking'] = dict ()

    # for every planner
    for iplanner in planners:

        matrix ['ranking'][iplanner] = dict ()

        # for every time step
        for itimelabel in timelabels:

            matrix ['ranking'][iplanner][itimelabel] = 0.0

            # compute the overall score of this planner at this particular
            # timing
            for idomain in domains:

                matrix ['ranking'][iplanner][itimelabel] += __score (scores[idomain][iplanner], itimelabel)

            # update the 'best' overall score found so far
            if (itimelabel not in best['ranking'].keys () or
                best['ranking'][itimelabel] < matrix['ranking'][iplanner][itimelabel]):

                best['ranking'][itimelabel] = matrix['ranking'][iplanner][itimelabel]                

        # compute the 'last' ranking of this planner
        last ['ranking'][iplanner] = __score (matrix['ranking'][iplanner])

    # explicitly specify sorting criteria, both for planners and the
    # timelabels. While the former are sorted in decreasing order of score, the
    # latter are sorted in lexicographical ordering ---since lexicographical
    # ordering has no parameters, none is passed; however, for sorting in
    # decreasing order of score, it is mandatory to pass by the vector with the
    # scores
    fcmpr     = score.initdata (['ranking'], score.cmplexicographical)
    fcmpc     = score.initdata (['ranking'], score.cmpvectorial)
    fcmpargsr = score.initdata (['ranking'], ())
    fcmpargsc = score.initdata (['ranking'], (last ['ranking'],))

    # besides, create the headers and footers at the corners of this table
    upperleft   = score.initdata (['ranking'], 'time')
    upperright  = score.initdata (['ranking'], 'best')
    bottomleft  = score.initdata (['ranking'], 'last')
    bottomright = score.initdata (['ranking'], '')

    # finally, return the matrix of scores and the column vector best and the
    # row vector last, along with the sorting criteria for rows (time stamps)
    # and columns (planners)
    return (matrix, best, last, fcmpr, fcmpc, fcmpargsr, fcmpargsc, \
            upperleft, upperright, bottomleft, bottomright)


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
                  domain, problem, time, labels, style, wxprogressdialog=None):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._directory, self._summary, self._metric, self._name, self._planner, 
         self._domain, self._problem, self._time, self._labels, self._style, wxprogressdialog) = \
         (directory, summary, metric, name, planner, 
          domain, problem, time, labels, style, wxprogressdialog)


    # Execute the following body when creating reports
    def __enter__ (self):
        """
        Execute the following body when creating the score tables
        """

        # before proceeding, check that all parameters are correct
        checkflags (self._directory, self._summary)


    # The following method sets up the environment for automating the creation
    # of score tables
    def tscore (self):
        """
        The following method sets up the environment for automating the creation
        of score tables
        """
        
        # generate the corresponding structure that contains all the information
        # from this directory
        (self._run, self._planners, self._domains, self._problems, self._track, self._subtrack) = \
            score.admindata (self._directory, self._summary, self._name, self._problem, self._domain, self._planner)

        # compute the precise time stamps when a planner solves a problem in any of
        # the selected domains
        self._timings = gettimings (self._run, self._planners, self._domains, self._problems, 
                                    self._time, self._labels)

        # now, decide what service to invoke as a function of the metric specified
        self._fcomp = {'quality'  : score.qualitydata,
                       'time0'    : score.time0data,
                       'time1'    : score.time1data,
                       'time2'    : score.time2data,
                       'solutions': score.solutionsdata,
                       'qt'       : score.qtdata} [self._metric]

        # and compute how the score evolves over the time period defined (MATRIX,
        (self._score, self._best, self._last, self._fcmpr, self._fcmpc, 
         self._fcmpargsr, self._fcmpargsc, self._upperleft, self._upperright, 
         self._bottomleft, self._bottomright) = \
         computeserie (self._run, self._planners, self._domains, self._problems, self._fcomp, self._timings)

        # now, in case that more than one domain has been requested
        if (len (self._domains) >= 1):

            # compute how the overall score for all planners/domains/problems
            # evolves over time from the data computed above ---note that gettimings
            # already computes the timings for the 'ranking' even if only one domain
            # is given
            (self._rkscore, self._rkbest, self._rklast, self._rkfcmpr, self._rkfcmpc, 
             self._rkfcmpargsr, self._rkfcmpargsc, 
             self._rkupperleft, self._rkupperright, self._rkbottomleft, self._rkbottomright) = \
             computeranking (self._planners, self._domains, self._score, self._timings ['ranking'])

            # copy all these values to a particular sheet ('ranking') in the same
            # params used for printing the resulting tables
            self._domains += ['ranking']
            (self._score ['ranking'], self._best ['ranking'], self._last ['ranking'],
             self._fcmpr ['ranking'], self._fcmpc ['ranking'], self._fcmpargsr ['ranking'], 
             self._fcmpargsc ['ranking'], self._upperleft ['ranking'], self._upperright ['ranking'], 
             self._bottomleft ['ranking'], self._bottomright ['ranking']) = \
            (self._rkscore ['ranking'], self._rkbest ['ranking'], self._rklast ['ranking'],
             self._rkfcmpr ['ranking'], self._rkfcmpc ['ranking'], 
             self._rkfcmpargsr ['ranking'], self._rkfcmpargsc ['ranking'],
             self._rkupperleft ['ranking'], self._rkupperright ['ranking'], self._rkbottomleft ['ranking'],
             self._rkbottomright ['ranking'])

        # finally, show the results in the corresponding format
        print score.tablestr (self._domains, self._score, self._best, self._last, 
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
                       ARGS.planner, ARGS.domain, ARGS.problem, ARGS.time, ARGS.labels, ARGS.style)

    # Now, enclose all the process in a with statement
    DISPATCHER = dispatcher (ARGS.directory, ARGS.summary, ARGS.metric, ARGS.name,
                             ARGS.planner, ARGS.domain, ARGS.problem, ARGS.time, ARGS.labels, ARGS.style)
    with DISPATCHER:
        
        # and request the generation of the report
        DISPATCHER.tscore ()



# Local Variables:
# mode:python
# fill-column:80
# End:
