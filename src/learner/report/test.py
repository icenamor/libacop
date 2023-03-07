#!/usr/bin/env python
#
# test.py
# Description: performs statistical tests on two series of data

# -----------------------------------------------------------------------------
#
# Started on  <Thu May 10 14:39:19 2012 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:10:18 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: test.py 322 2012-07-16 07:59:19Z clinares                            $
# $Date:: 2012-07-16 09:59:19 +0200 (lun 16 de jul de 2012)                  $
# $Revision:: 322                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@korf.plg.inf.uc3m.es>
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
performs statistical tests on two series of data
"""

__version__  = '1.3'
__revision__ = '$Revision: 322 $'
__date__     = '$Date: 2012-07-16 09:59:19 +0200 (lun 16 de jul de 2012) $'

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import getopt           # variable-length params
import os               # path and process management
import re               # regular expressions
import sys              # argv, exit

import IPCrun           # for storing info about different runs
import IPCtest          # services for performing statistical tests

import report           # IPC reporting services

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.3"

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
    parser = argparse.ArgumentParser (description="performs statistical tests on two series of data")
    
    # now, add the arguments
    
    # Group of mandatory arguments
    mandatory = parser.add_argument_group ("Mandatory arguments", "The following arguments are mandatory. They do set up the type of statistical analysis to be performed")
    mandatory.add_argument ('-t', '--test',
                            nargs = '*',
                            default = ['mw'],
                            choices=['mw','tt','wx','bt'],
                            help='sets up the type of statistical analysis to be performed. Use the directive --tests to see an explanation of all kinds of tests. It is possible to define as many as desired. Mann-Whitney U is used by default')
    
    # Group of alternative arguments
    alternative = parser.add_argument_group ("Alternative arguments", "The following arguments define alternative ways to access data. Note that it is not legal to use both arguments simultaneously but one has to be provided")
    alternative.add_argument ('-d', '--directory',
                              help='specifies a directory to explore')
    alternative.add_argument ('-s', '--summary',
                              help="reads a snapshot or summary previously generated with 'report.py'")
    
    # Group of filtering arguments
    filtering = parser.add_argument_group ("Filtering", "The following directives provide various means to filter the data to be considered in the statistical test. Data is retrieved with the script 'report.py'. The leftmost column (as returned by the IPC 'report'.py script) stands for the names of the series to analyze whereas the rightmost column contains the data to compare")
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
    filtering.add_argument ('-v', '--variable',
                            nargs=1,
                            help='explicitly requests the value of the given variable. For a full list of variables use the directive --variables. Only one variable can be specified')
    filtering.add_argument ('-f', '--filter',
                            nargs=1,
                            default=None,
                            help='only the rows that match the filter are selected. A filter consists of the name of a single variable that has to be True for it to be selected. If the filter variable is False, the variable is still passed to the statistical analysis with the value NOENTRY which can be overwritten with --noentry. When creating pairwise associations, unfiltered entries are treated according to the option given to --matcher')
    filtering.add_argument ('-m', '--matcher',
                            choices=['and','or','all'],
                            default='all',
                            help="when matching two series to perform the statistical test, pairwise associations are computed. If 'and' is provided, only filtered values are preserved; if 'or' is given, only those pairs where at most one entry has not been filtered are processed. If 'all ' is provided, all pairs are accepted. 'all' is used by default")
    filtering.add_argument ('-e', '--noentry',
                            metavar='INTEGER',
                            type=int,
                            default=IPCtest.NOENTRY,
                            help="if entries are filtered with --filter, those that are unfiltered get the value NOENTRY. However, in some cases it is desirable to give them a particular value. This value sets the value of NOENTRY to any integer value")
    
    # Group of appearance arguments
    appearance = parser.add_argument_group ("Appearance", "The following arguments modify in one way or another how data is collected and presented")
    appearance.add_argument ('-n','--name',
                             default='report',
                             help='name of the output table. By default "report"')
    appearance.add_argument ('-l','--level',
                             choices=['problem','domain','planner','track'],
                             help='shows the results at the specified level. If none is given, the level is automatically derived from the depth of the directory given or the directory of the snapshot specified')
    appearance.add_argument ('-u', '--unroll',
                             action='store_true',
                             default=False,
                             help='if the values of an arbitrary number of variables can be iterated (e.g., lists), this flag forces each row to be "unzipped" to an arbitrary number of rows, the ith one showing the ith item of each value. False, by default')
    appearance.add_argument ('-K','--ascending',
                             nargs=0,
                             metavar='key',
                             dest='sorting',
                             action=KeyAction,
                             help='if provided, the values are sorted in increasing order of the values of the variable specified with --variable. Besides, it is also feasible to sort the values on various keys. Legal keys are "problem", "domain", "planner" and "track"')
    appearance.add_argument ('-k','--descending',
                             nargs=0,
                             metavar='key',
                             dest='sorting',
                             action=KeyAction,
                             help='if provided, the values are sorted in increasing order of the values of the variable specified with --variable. Besides, it is also feasible to sort the values on various keys. Legal keys are "problem", "domain", "planner" and "track"')
    appearance.add_argument ('-y', '--style',
                             default='table',
                             choices=['table','octave','html','excel','wiki'],
                             help='sets the report style')
    
    # Group of miscellaneous arguments
    misc = parser.add_argument_group ('Miscellaneous')
    misc.add_argument ('-x','--variables',
                       nargs=0,
                       action=report.ShowAction,
                       help='shows a comprehensive list of variables recognized by this script')
    misc.add_argument ('-T','--tests',
                       nargs=0,
                       action=ShowAction,
                       help='shows a comprehensive list of all the available statistical tests')
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
# KeyAction
#
# adds a key for sorting the output report. Every key is given just a
# variable. This action adds either (value, '<') or (value, '>') to the dest
# attribute which is 'sorting'
# -----------------------------------------------------------------------------
class KeyAction (argparse.Action):
    """
    adds a key for sorting the output report. Every key is given just a
    variable. This action adds either (value, '<') or (value, '>') to the dest
    attribute which is 'sorting'
    """

    def suffix (self, option_string):
        return {'-K': '<',
                '--ascending': '<',
                '-k': '>',
                '--descending': '>'} [option_string]

    def __call__(self, parser, namespace, values, option_string=None):

        setattr (namespace, 'sorting', self.suffix (option_string))


# -----------------------------------------------------------------------------
# ShowAction
#
# shows a comprehensive list of all the available statistical tests
# -----------------------------------------------------------------------------
class ShowAction (argparse.Action):
    """
    shows a comprehensive list of all the available statistical tests
    """

    def __call__(self, parser, namespace, values, option_string=None):

        print "\n %s\n" % ('-'*100)

        for itest in range (0, IPCtest.NBTESTS):

            print " %s (--test %s):\n %s\n" % (IPCtest.TESTS [itest], IPCtest.ACRONYMS [itest],
                                               IPCtest.DESCS [itest])

        print " %s\n" % ('-'*100)

        # and finally exit
        sys.exit (0)
        

# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params.
# -----------------------------------------------------------------------------
def show_switches (summary, tests, name, level, planner, domain, \
                       problem, variable, vfilter, matcher, noentry, unroll, sorting, style):

    """
    show a somehow beautified view of the current params. The output is directed
    to the specified logger
    """

    # compute the level
    levelname = None
    if (level):
        levelname = IPCrun.LEVELS [level]

    # compute the list of sorting keys/variables
    sortlist = list ()
    if (sorting):
        for isorting in sorting:
            sortlist.append ("%s (%s)" % (isorting [0],
                                          {False: "descending", 
                                           True:  "ascending"}[isorting [1]=='<']))

    # compute the names of all the tests requested
    if (tests):
        teststr = map (lambda x:IPCtest.TESTS [x], tests)
    else:
        teststr = ''

    print (""" -----------------------------------------------------------------------------
 * snapshot       : %s
 * tests          : %s
 * name           : %s
 * level          : %s
 * planner        : %s
 * domain         : %s
 * problem        : %s
 * variable       : %s
 * filter         : %s
 * matcher        : %s
 * noentry        : %s
 * unroll         : %s
 * sorting        : %s
 * style          : %s
 -----------------------------------------------------------------------------\n""" % (summary, teststr, name, levelname, planner, domain, problem, variable, vfilter, matcher, noentry, unroll, sortlist, style))


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
# getseries
#
# returns the series to analyze from the contents of the IPC run in table
# format. The results are described in a dictionary whose keys are the names of
# the serie and whose values are the list of values to compare. In case a filter
# is provided, then only those entries that match it are selected. Otherwise,
# False is inserted instead
# -----------------------------------------------------------------------------
def getseries (contents, vfilter = None):

    """
    returns the series to analyze from the contents of the IPC run in table
    format. The results are described in a dictionary whose keys are the names
    of the serie and whose values are the list of values to compare. In case a
    filter is provided, then only those entries that match it are
    selected. Otherwise, False is inserted instead
    """

    # initialization
    series = {}

    # for all contents
    for icontent in contents:

        # check whether the first item in this content is already known or not
        if (icontent [0] not in series):

            # if not, reserve room to store a new serie
            series [icontent [0]] = list ()

        # add the last value in this content to the corresponding serie in case
        # it matches the filter or none is provided. If a filter has been
        # provided, its value is writen the beforelast position
        if (not vfilter or 
            (vfilter and icontent [-2])):
            series [icontent [0]].append (icontent [-1])
        else:
            series [icontent [0]].append (IPCtest.NOENTRY)

    # and return the series computed this way
    return series


# -----------------------------------------------------------------------------
# dispatcher
#
# this class creates a dispatcher for automating the statistical tests
# -----------------------------------------------------------------------------
class dispatcher (object):
    """
    this class creates a dispatcher for automating the statistical tests
    """

    # Default constructor
    def __init__ (self, test, directory, summary, name, level,
                  planner, domain, problem, variable, 
                  vfilter, matcher, noentry, unroll, sorting,
                  style, wxProgressDialog=None):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._test, self._directory, self._summary, self._name, self._level,
         self._planner, self._domain, self._problem, self._variable, 
         self._filter, self._matcher, self._noentry, self._unroll, self._sorting, 
         self._style, self._wxProgressDialog) = \
         (test, directory, summary, name, level,
          planner, domain, problem, variable, 
          vfilter, matcher, noentry, unroll, sorting, 
          style, wxProgressDialog)

        # Initialize the information returned by the reporter
        self._run = None

        # Update the PROGRAM_NAME of the IPC reporter
        report.PROGRAM_NAME = 'report.py'
 

    # Execute the following body when entering the block
    def __enter__ (self):
        """
        Execute the following body when entering the block
        """

        pass


    # The following method sets up the environment for automating the statistical tests
    def test (self):
        """
        The following method sets up the environment for automating the statistical tests
        """

        # First of all, retrieve all the data from the IPC reporting tool. The
        # variables requested to the reporter also include the filter, in case
        # any has been specified.
        if (self._filter):
            variables = self._filter + self._variable
        else:
            variables = self._variable

        # launch the query
        reporter = report.dispatcher (self._directory, self._summary, None, 'report', self._level,
                                      self._planner, self._domain, self._problem, variables, 
                                      self._unroll, self._sorting, self._style)
        with reporter:
            
            # and request the generation of the report
            reporter.report ()
        
            # and now, retrieve the data reported
            self._run = reporter.get_run ()

            # now, get the series to analyze. These shall be represented with a
            # dictionary whose key are the names of the series and whose values
            # are the series to analyze
            self._series = getseries (self._run.tablify (), self._filter)

        # next, create an IPCtestsheet to perform all the statistical tests and
        # to print them out
        tests = IPCtest.IPCtests (self._series, self._test, self._matcher, self._noentry)
        tests.set_format (eval ("IPCtest.%s" % self._style.upper ()))
        tests.set_name (self._name)
        tests.tests ()
        print tests


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

    # convert the string level to the right value
    LEVEL = {None     : None,
             'problem': IPCrun.TRK_PLN_DMN_PRB, 
             'domain' : IPCrun.TRK_PLN_DMN,
             'planner': IPCrun.TRK_PLN,
             'track'  : IPCrun.TRK} [ARGS.level]

    # process the command line options for the tests selection and convert them
    # into the right values
    ARGS.test = map (lambda x:{'mw': IPCtest.MANNWHITNEYU, 
                               'tt': IPCtest.TTEST, 
                               'wx': IPCtest.WILCOXON, 
                               'bt': IPCtest.BINOMIAL}[x],
                     ARGS.test)

    # besides, translate the sorting values (in case they are provided) to the
    # same format acknowledged by report.py, a list with a single tuple of the
    # form (variable name, <|>)
    if (ARGS.sorting):
        setattr (ARGS, 'sorting',[(ARGS.variable [0], ARGS.sorting)])

    # show the current version and also a comprehensive view of the current switches
    if (not ARGS.quiet):
        version ()
        show_switches (ARGS.summary, ARGS.test, ARGS.name, LEVEL, ARGS.planner, ARGS.domain, 
                       ARGS.problem, ARGS.variable, ARGS.filter, ARGS.matcher, ARGS.noentry, 
                       ARGS.unroll, ARGS.sorting, ARGS.style)

    # Now, retrieve the values selected with the command-line arguments using
    # the IPC report and proceed to perform the statistical analysis
    TESTER = dispatcher (ARGS.test, None, ARGS.summary, ARGS.name, LEVEL,
                         ARGS.planner, ARGS.domain, ARGS.problem, ARGS.variable, 
                         ARGS.filter, ARGS.matcher, ARGS.noentry, ARGS.unroll, 
                         ARGS.sorting, ARGS.style)
    with TESTER:
        
        # and request the extraction of data and the realization of the statistical test
        TESTER.test ()




# Local Variables:
# mode:python
# fill-column:80
# End:
