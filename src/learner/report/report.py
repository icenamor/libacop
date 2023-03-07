#!/usr/bin/env python
#
# report.py
# Description: creates a report of an arbitrary level

# -----------------------------------------------------------------------------
#
# Started on  <Tue Apr 12 14:03:04 2011 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:10:04 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: report.py 321 2012-07-15 14:21:33Z clinares                          $
# $Date:: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012)                  $
# $Revision:: 321                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@Ceres.local>
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
creates a report of an arbitrary level
"""

__version__  = '1.3'
__revision__ = '$Revision: 321 $'
__date__     = '$Date: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012) $'

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import getopt           # variable-length params
import os               # path and process management
import re               # regular expressions
import sys              # argv, exit

import IPCrun           # for storing info about different runs
import reportl0         # for handling depth0 directories

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
    parser = argparse.ArgumentParser (description="Creates a report of an arbitrary level")
    
    # now, add the arguments
    
    # Group of alternative arguments
    alternative = parser.add_argument_group ("Alternative arguments", "The following arguments define alternative ways to access data. Note that it is not legal to use both arguments simultaneously but one has to be provided")
    alternative.add_argument ('-d', '--directory',
                              help='specifies a directory to explore')
    alternative.add_argument ('-s', '--summary',
                              help='reads a snapshot or summary previously generated with the option --summarize')
    
    # Group of additional actions
    actions = parser.add_argument_group ("Additional Actions", "The following directive requests this module to perform additional actions other than just generating the requested report")
    actions.add_argument ('-z','--summarize',
                          help='creates a summary (or snapshot) of the results found at the given directory and stores them in a binary file that can be later reused with --summary. This results in an improved performance over --directory')
    
    # Group of filtering arguments
    filtering = parser.add_argument_group ("Filtering", "The following directives provide various means to filter the data to appear in the report")
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
                            nargs='+',
                            help='explicitly requests the value of the given variable. For a full list of variables use the directive --variables. It is possible to provide an arbitrary number of variables. Variables are shown in the same order they are specified')
    
    # Group of appearance arguments
    appearance = parser.add_argument_group ("Appearance", "The following arguments modify in one way or another how data is presented")
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
                             nargs='+',
                             metavar='key',
                             dest='sorting',
                             default = [],
                             action=KeyAction,
                             help='if either a key or a variable given with --variable is used with this flag, the output is sorted in ascending order according to this key/variable. It is possible to provide an arbitrary number of variables/keys. Legal keys are "problem", "domain", "planner" and "track"')
    appearance.add_argument ('-k','--descending',
                             nargs='+',
                             metavar='key',
                             dest='sorting',
                             action=KeyAction,
                             help='if either a key or a variable given with --variable is used with this flag, the output is sorted in descending order according to this key/variable. It is possible to provide an arbitrary number of variables/keys. Legal keys are "problem", "domain", "planner" and "track"')
    appearance.add_argument ('-y', '--style',
                             default='table',
                             choices=['table','octave','html','excel','wiki'],
                             help='sets the report style')
    
    # Group of miscellaneous arguments
    misc = parser.add_argument_group ('Miscellaneous')
    misc.add_argument ('-x','--variables',
                       nargs=0,
                       action=ShowAction,
                       help='shows a comprehensive list of variables recognized by this script')
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
# shows a comprehensive list of legal variables recognized by this script. This
# is enclosed within a class definition to allow the automatic execution from
# the command-line parsing arguments
# -----------------------------------------------------------------------------
class ShowAction (argparse.Action):
    """
    shows a comprehensive list of legal variables recognized by this
    script. This is enclosed within a class definition to allow the automatic
    execution from the command-line parsing arguments
    """

    def __call__(self, parser, namespace, values, option_string=None):
        print """
  id      name                      description
 %s+%s+%s""" % ('-'*4, '-'*14, '-'*96)

        for ivar in range (0, IPCrun.NUMVARS):
            print "  %02i |%14s| %s" % (ivar, IPCrun.VARS[ivar], IPCrun.DESCS[ivar])
            if (ivar>0 and ivar%5==0 and ivar!=IPCrun.NUMVARS-1):
                print " %s+%s+%s" % ('-'*4, '-'*14, '-'*96)

        print """ %s+%s+%s

 variables shall be referred by their name when using the flag --variable
 use the directive --help for more information
""" % ('-'*4, '-'*14, '-'*96)

        # and finally exit
        sys.exit (0)
        

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

        # process all values
        lvalues = map (lambda x:(x, self.suffix (option_string)), values)

        # if the attribute 'sorting' is empty
        if (not vars (namespace) ['sorting']):
            
            # then initialize it
            setattr (namespace, 'sorting', lvalues)

        # otherwise
        else:

            # append it
            setattr (namespace, 'sorting', vars (namespace) ['sorting'] + lvalues)


# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params.
# -----------------------------------------------------------------------------
def show_switches (directory, summary, summarize, name, level, planner, domain, \
                       problem, variables, unroll, sorting, style):

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

    print (""" -----------------------------------------------------------------------------
 * %-15s: %s
 * snapshot       : %s
 * name           : %s
 * level          : %s
 * planner        : %s
 * domain         : %s
 * problem        : %s
 * variables      : %s
 * unroll         : %s
 * sorting        : %s
 * style          : %s
 -----------------------------------------------------------------------------\n""" % ({False:'summary', True:'directory'}[bool (directory)], {False:summary, True:directory}[bool (directory)], summarize, name, levelname, planner, domain, problem, variables, unroll, sortlist, style))


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
def checkflags (directory, summary, summarize, variables, sorting):

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

    if (summarize and os.access (summarize, os.F_OK)):
        print """
 The summary file provided does exist! Rename it or choose a different filename
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    if (summarize and not os.access (os.path.dirname (summarize), os.X_OK)):
        print """
 It is not possible to access the directory '%s'
 Type '%s --help' for more information
""" % (os.path.dirname(summarize), PROGRAM_NAME)
        raise ValueError

    # now, check at least one variable has been provided
    if (not variables):
        print """
 Please, provide at least one variable to examine
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    for ivar in variables:
        
        try:
            index = eval ("IPCrun."+ivar.upper ())

        except:
            print """
 Fatal Error - Unrecognized variable '%s'
               type '%s --variables' to get a comprehensive list of available variables
""" % (ivar, PROGRAM_NAME)
            sys.exit ()


    # check the keys/variables used for sorting
    if (sorting):
        for isorting in sorting:
            if (isorting[0] not in ["problem", "domain", "planner", "track"] + variables):
                print """
     Fatal Error - '%s' is neither a key nor a variable specified with --variable
                   type '%s --help' for more information
    """ % (isorting [0], PROGRAM_NAME)
                sys.exit ()


# -----------------------------------------------------------------------------
# guessdepth
#
# guess the depth of the specified directory: depth 0 for problems; depth 1 for
# domains; depth 2 for planners and depth 3 for track-subtracks
# -----------------------------------------------------------------------------
def guessdepth (directory, depth=0):

    """
    guess the depth of the specified directory: depth 0 for problems; depth 1
    for domains; depth 2 for planners and depth 3 for track-subtracks
    """

    # guessing is done recursively: 

    # case base - this directory is depth 0

    # general case - this directory is depth i if and only if *all* its
    # subdirectories are depth (i-1). Since the maximum depth is 4, there is no
    # need to recursively examine more than 4 depths so that the variable
    # "depth" is passed to the descendants to keep track of the length of the
    # path currently under consideration

    # exit condition
    
    # although this script computes the depth when propagating the 0s upwards,
    # it also receives provisional depths from the upper levels. Therefore, if
    # we are now too far from the original root we know for sure that the value
    # propagated upwards will be illegal so an error can be issued at this point
    if (depth > IPCrun.TRK):

        raise NameError, "The directory '%s' exceeds the maximum depth" % directory

    # check whether this is a depth 0 or not
    try:

        (logfile, vallogfile, planner, domain, problem) = \
            reportl0.checkdepth0 (directory, error=False)

        # if this succeded, return depth 0
        return IPCrun.TRK_PLN_DMN_PRB

    # if the above attempt failed, do nothing
    except Exception, message:
        pass
        
    # so this is known to be a non-zero depth, so recursively examine all the
    # subdirectories beneath this one
    subdirs = []
    subdepths = list ()       # create a list for storing the depth of all descendants
    for root, dirnames, filenames in os.walk (directory):
        if (root == directory):
            subdirs = filter (lambda x : x[0]!='.' and x[0]!='_', dirnames)

    if (len (subdirs) == 0):
        print " Fatal Error - The directory '%s' does not exist!" % directory
        raise NameError, " The directory '%s' does not exist!" % directory

    for isubdir in subdirs:

        try:

            subdepth = guessdepth (directory + '/' + isubdir, depth + 1)
            
            # if we went too far return an error
            if (subdepth == -1):
                return -1
            else:
                subdepths.append (subdepth)

        # if an exception was raised from the previous recursive call, just
        # ignore it
        except Exception, message:
            pass

    # now, if all subdirs are of the same depth, ...
    if (len (subdepths) > 0 and len (filter (lambda x:x!=subdepths[0], subdepths)) == 0):
        
        # then the depth of this directory is the depth of the subdirectories
        # plus one
        return subdepths[0] + 1

    # Otherwise, directories with different depths have been found, return an error
    return -1

    
# -----------------------------------------------------------------------------
# depthp
#
# parses all subdirs beneath the specified one that match the corresponding
# regexps and computes the requested variables at the specified level. The
# resulting table is named after "name"
#
# if warning is given, a warning message is issued everytime a
# particular information is not found
# -----------------------------------------------------------------------------
def depthp (directory, name, variables, unroll, sorting, regexps, level, depth, warning=False):

    """
    parses all subdirs beneath the specified one that match the corresponding
    regexps and computes the requested variables at the specified level. The
    resulting table is named after 'name'
    
    if warning is given, a warning message is issued everytime a
    particular information is not found
    """

    # create a glossary of variables for storing the information of all
    # variables at this depth with the specified name and sorting schema
    data = IPCrun.IPCrun (depth, level)
    data.set_name (name)
    data.set_unroll (unroll)
    data.set_sorting (sorting)

    # get a list of all the subdirs beneath this one
    for root, dirnames, filenames in os.walk (directory):
        if (root == directory):
            subdirs = sorted (filter (lambda x : x[0]!='.' and x[0]!='_', dirnames))

    # now, process all the subdirs
    for isubdir in subdirs:

        # only in case this directory matches the given regexp
        if re.match (regexps[depth-1], isubdir):

            # get information on *all* vars for this particular subdir
            run = processdepth (directory + '/' + isubdir, name, variables, unroll, \
                                sorting, regexps, level, depth - 1, warning)

            # "accumulate" information on the raw variables just updating
            # the current 'run' with a new *single* key which is, indeed,
            # the examined subdir
            data += run.prefix (isubdir)

    # and return it
    return data


# -----------------------------------------------------------------------------
# processdepth
#
# it invokes the right service depending upon the specified depth
# -----------------------------------------------------------------------------
def processdepth (directory, name, variables, unroll, sorting, regexps, level, depth, warning=False):
    """
    it invokes the right service depending upon the specified depth
    """

    if (depth == 0):
        run = reportl0.depth0 (directory, name, variables, unroll, warning)
    else:
        run = depthp (directory, name, variables, unroll, sorting, regexps, level, depth, warning)

    return run


# -----------------------------------------------------------------------------
# dispatcher
#
# this class creates a dispatcher for automating the creation of reports
# -----------------------------------------------------------------------------
class dispatcher (object):
    """
    this class creates a dispatcher for automating the creation of reports
    """

    # Default constructor
    def __init__ (self, directory, summary, summarize, name, level,
                  planner, domain, problem, variable, unroll, 
                  sorting, style, wxProgressDialog=None):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._directory, self._summary, self._summarize, self._name, self._level,
         self._planner, self._domain, self._problem, self._variable, self._unroll, 
         self._sorting, self._style, self._wxProgressDialog) = \
         (directory, summary, summarize, name, level,
          planner, domain, problem, variable, unroll, 
          sorting, style, wxProgressDialog)

        # Initialize the information selected by this particular selection of
        # arguments
        self._run = None


    # Execute the following body when creating reports
    def __enter__ (self):
        """
        Execute the following body when creating reports
        """

        # before proceeding, check that all parameters are correct
        checkflags (self._directory, self._summary, self._summarize, self._variable, self._sorting)


    # The following method sets up the environment for automating the creation of reports
    def report (self):
        """
        The following method sets up the environment for automating the creation of reports
        """

        # if a summary was provided, deserialize its contents to recreate the original run
        if (self._summary):
            self._run = IPCrun.IPCrun ()
            self._run.deserialize (self._summary)

            # now, modifiy the information stored in the summary/snapshot with the
            # flags provided by the user
            if (self._variable):

                # now, make sure that only the specified variables are enabled
                self._run.disable_all ()
                map (lambda ivar:self._run.enable (eval ("IPCrun."+ivar.upper ())), self._variable)

            # filter the contents of this run to contain only those specified in the
            # command line
            if (self._planner != '.*' or self._domain != '.*' or self._problem != '.*'):
                self._run.filter ({IPCrun.TRK             : self._planner,
                                   IPCrun.TRK_PLN         : self._domain,
                                   IPCrun.TRK_PLN_DMN     : self._problem,
                                   IPCrun.TRK_PLN_DMN_PRB : '.*'})

            # set other parameters that affect the behaviour of this run in case
            # the user provided non-default values
            self._run.set_unroll (self._unroll)
            if (self._level):
                self._run.set_level (self._level)
            if (self._name!='report'):
                self._run.set_name (self._name)
            if (self._style != 'table'):
                self._run.set_format (eval ("IPCrun." + self._style.upper ()))
            if (self._sorting):
                self._run.set_sorting (self._sorting)

        # otherwise, process the given directory
        else:

            # guess the corresponding depth of the specified directory
            self._depth = guessdepth (self._directory)
            if (self._depth < 0):
                print """
 Fatal Error - The directory '%s' does not seem to belong to the 'results' hierarchy
        """ % self._directory
                sys.exit ()

            # at depth 0 make sure that no elaborated data has been requested
            if (self._depth == 0 or self._level == 0):
                for ivar in self._variable:
                    idx = eval ("IPCrun." + ivar.upper ())
                    if (IPCrun.iselaborated (idx)):
                        print """
 Fatal Error - Variable '%s' is elaborated and elaborated data is explicitly forbidden at depth/level 0
        """ % ivar
                        sys.exit ()

            # if no level has been specified, take the depth by default
            if (self._level==None):
                self._level = self._depth

            # if the requested level is above the current depth, then issue an error
            # ---it does not make sense to request data at the level of planner for
            # instance, providing a directory which is at the depth of a domain
            if (self._level > self._depth):
                print """
 Fatal Error - The specified level '%s' is above the given directory '%s'
        """ % (IPCrun.LEVELS [self._level], self._directory)
                sys.exit ()

            self._run = processdepth (self._directory, self._name, self._variable, self._unroll, 
                                      self._sorting, [self._problem, self._domain, self._planner, '.*'], 
                                      self._level, self._depth, warning=False)

        # and now, if a summarize has been provided, serialize its contents
        if (self._summarize):
            self._run.serialize (self._summarize)


    # The following method returns the information queried by the selection of
    # the parameters given to this class
    def get_run (self):
        """
        The following method returns the information queried by the selection of
        the parameters given to this class
        """

        return self._run


    # The following method prints out the results of the query in the specified
    # format
    def show (self):
        """
        The following method prints out the results of the query in the specified
        format
        """

        # set the specified style
        if (self._style == 'table'):
            self._run.set_format (IPCrun.TABLE)
        elif (self._style == 'octave'):
            self._run.set_format (IPCrun.OCTAVE)
        elif (self._style == 'html'):
            self._run.set_format (IPCrun.HTML)
        elif (self._style == 'excel'):
            self._run.set_format (IPCrun.EXCEL)
        elif (self._style == 'wiki'):
            self._run.set_format (IPCrun.WIKI)
        else:
            print """
 Unrecognized style '%s'
     """ % STYLE
            sys.exit ()        

        # and finally print it out

        print self._run
            

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

    # show the current version and also a comprehensive view of the current switches
    if (not ARGS.quiet):
        version ()
        show_switches (ARGS.directory, ARGS.summary, ARGS.summarize, ARGS.name, LEVEL, ARGS.planner, 
                       ARGS.domain, ARGS.problem, ARGS.variable, ARGS.unroll, ARGS.sorting, ARGS.style)

    # Now, enclose all the process in a with statement
    DISPATCHER = dispatcher (ARGS.directory, ARGS.summary, ARGS.summarize, ARGS.name, LEVEL,
                             ARGS.planner, ARGS.domain, ARGS.problem, ARGS.variable, ARGS.unroll, 
                             ARGS.sorting, ARGS.style)
    with DISPATCHER:
        
        # and request the generation of the report
        DISPATCHER.report ()

        # and print it
        DISPATCHER.show ()


# Local Variables:
# mode:python
# fill-column:80
# End:
