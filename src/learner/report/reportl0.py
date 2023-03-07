#!/usr/bin/env python
#
# report.py
# Description: creates a report of a depth 0 directory, this is, a
#              track-subtrack-planner-domain-problem
# -----------------------------------------------------------------------------
#
# Started on  <Mon Apr  4 13:08:04 2011 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:09:59 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: reportl0.py 321 2012-07-15 14:21:33Z clinares                        $
# $Date:: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012)                 $
# $Revision:: 321                                                            $
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
creates a report of a depth 0 directory, this is, a track-subtrack-planner-domain-problem
"""

__version__  = '1.3'
__revision__ = '$Revision: 321 $'
__date__     = '$Date: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012) $'

# imports
# -----------------------------------------------------------------------------
import getopt           # variable-length params
import os               # path and process management
import re               # regular expressions
import sys              # argv, exit

import IPCrun           # for storing info about different runs

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.3"

# regular expressions
#LOGREGEXP = '_(?P<track>[a-z]+)-(?P<subtrack>[a-z]+)\.(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-log'
LOGREGEXP = '_(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-log'
TIMEREGEXP       = '^ Timeout: (?P<timeout>[0-9]+) seconds'
MEMREGEXP        = '^ Memory : (?P<memory>[0-9]+) bytes'
RUNTIMEREGEXP    = '^ Overall runtime: (?P<runtime>[0-9]+) seconds'
MEMENDREGEXP     = '^ Overall memory : (?P<memend>[0-9\.]+) Mbytes'
MEMMAXREGEXP     = '^ Maximum memory : (?P<memmax>[0-9\.]+) Mbytes'
NUMSOLSREGEXP    = '^ Number of solutions found: (?P<numsols>[0-9]+)'

TIMELABELREGEXP  = '^ \\[real-time [0-9]+\\] total_time: (?P<timelabel>[0-9\.]+)'
MEMLABELREGEXP   = '^ \\[real-time [0-9]+\\] total_vsize: (?P<memlabel>[0-9\.]+)'
TIMESOLREGEXP    = '^ Time/solution.*:.*\\[(?P<timesollabel>[0-9, ]+)\\]'

#VALLOGREGEXP = '_(?P<track>[a-z]+)-(?P<subtrack>[a-z]+)\.(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-val'
VALLOGREGEXP = '_(?P<planner>([a-zA-Z0-9-_]+|[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+))-(?P<domain>[a-zA-Z-]+).(?P<problem>[0-9]+)-val'
VALNUMSOLS       = '^ Number of solution files found: (?P<valnumsols>[0-9]+)'
OKNUMSOLS        = '^ Number of correct solutions found: (?P<oknumsols>[0-9]+)'
PLANSOLN         = '^ Solution file: (?P<plansoln>[A-za-z0-9\.]+[0-9]*)'
VALUE            = '^ Value.*: (?P<value>[-|+]*[0-9]+[\.0-9]*)'
LENGTH           = '^ Step length.*: (?P<length>[-|+]*[0-9]+)'

# -----------------------------------------------------------------------------

# Funcs
# -----------------------------------------------------------------------------

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

    if 'error' is given, an error message is issued when a given file is not
    found
    """

    # the minimal files are the '-log' file and the pddl files
    if ('domain.pddl' not in os.listdir (directory)):
        if error:
            print """
 Error - Domain file 'domain.pddl' has not been found in %s""" % directory
        raise KeyError, 'domain.pddl'

    if ('problem.pddl' not in os.listdir (directory)):
        if error:
            print """
 Error - Problem file 'problem.pddl' has not been found in %s""" % directory
        raise KeyError, 'problem.pddl'

    # look for the log file
    logfile = filter (lambda x : re.match(LOGREGEXP,x), os.listdir (directory))

    if (len (logfile) == 0):
        if error:
            print """
 Error - No '-log' file has been found at %s""" % directory
        raise KeyError, 'problem.pddl'        

    if (len (logfile) > 1):
        if error:
            print """
 Error - more than one '-log' file has been found at %s: %s""" % (directory, logfile)
        raise IndexError, logfile

    # now, look for the val log file
    vallogfile = filter (lambda x : re.match(VALLOGREGEXP,x), os.listdir (directory))

    if (len (vallogfile) > 1):
        if error:
            print """
 Error - more than one '-val' file has been found at %s: %s""" % (directory, vallogfile)
        raise IndexError, vallogfile

    if (len (vallogfile) == 0):
        vallogfilename = None
    else:
        vallogfilename = vallogfile [0]

    # at this point, this directory is accepted as depth0 and the name of the
    # log file along with other data is returned
    m = re.match (LOGREGEXP, logfile [0])
    return ( logfile [0], vallogfilename, \
                 m.group ('planner'), m.group ('domain'), m.group ('problem') )

    
# -----------------------------------------------------------------------------
# parsefield0
#
# looks for a specific regx in a list of lines and return the value of the
# specified tag as a list. If warning is specified, a warning is issued if a
# line does not match the given regexp explicitly indicating the logfile
# -----------------------------------------------------------------------------
def parsefield0 (regexp, tag, L, logfile, warning=False):

    """
    looks for a specific regx in a list of lines and return the value of the
    specified tag as a list. If warning is specified, a warning is issued if a
    line does not match the given regexp
    """

    # first, take only those lines that match the given expression
    lines = filter (lambda x : re.match (regexp, x), L)

    # if none is found, raise an error
    if (not len (lines)):

        if (warning):
            print " Warning - No line matched the expresion '%s' in '%s'" % (regexp, logfile)

        # anyway, raise an exception, since the next line does not make sense
        raise NameError, regexp

    # now, map all lines to their respective tag values
    return [m.group (tag) for m in [re.match (regexp, iline) for iline in lines]]


# -----------------------------------------------------------------------------
# parselogdepth0
#
# parses the contents of a log file and retrieves its contents. If warning is
# specified, a warning is issued everytime a given line does not match a
# particular regexp
# -----------------------------------------------------------------------------
def parselogdepth0 (directory, logfile, warning=False):

    """
    parses the contents of a log file and retrieves its contents. If warning is
    specified, a warning is issued everytime a given line does not match a
    particular regexp
    """

    # get the contents of the logfile (which is known to exist)
    logpathfile = directory + '/' + logfile
    logstream = open (logpathfile, 'r')
    lines = logstream.readlines ()

    # get the time bound, memory bound, overall runtime, overall memory and
    # maximum memory ---all these values are mandatory and shall appear always!
    # Thus, if none is found an exception is raised
    try:
        timeout    = int   (parsefield0 (TIMEREGEXP, 'timeout', lines, logpathfile, warning)[0])
        memory     = int   (parsefield0 (MEMREGEXP, 'memory', lines, logpathfile, warning)[0])
        runtime    = int   (parsefield0 (RUNTIMEREGEXP, 'runtime', lines, logpathfile, warning)[0])
        memend     = float (parsefield0 (MEMENDREGEXP, 'memend', lines, logpathfile, warning)[0])
        memmax     = float (parsefield0 (MEMMAXREGEXP, 'memmax', lines, logpathfile, warning)[0])

    except:
        print " Fatal exception raised while getting one of the primitive values"
        exit ()

    # now, in case any solution has been found, report the number of solutions
    # found and the time ticks when they were found
    try:
        numsols    = 0
        timesols   = list ()
        numsols    = int   (parsefield0 (NUMSOLSREGEXP,'numsols', lines, logpathfile, warning)[0])
        timesols   = [int (reading)
                      for reading in [filter (lambda x:x!=',', ith)
                                      for ith in \
                                      parsefield0 (TIMESOLREGEXP, 'timesollabel', lines, logpathfile, warning)[0].split ()]]
        timesols = sorted (timesols)
    except:
        pass

    # do also retrieve the memory usage profile
    try:
        timelabels = memlabels = list ()
        timelabels = parsefield0 (TIMELABELREGEXP, 'timelabel', lines, logpathfile, warning)
        memlabels  = parsefield0 (MEMLABELREGEXP, 'memlabel', lines, logpathfile, warning)
        
    except NameError:
        pass
    except Exception:
        print " Fatal exception raised while parsing the memory usage profile"
        exit ()
        
    # close and exit
    logstream.close ()

    # and return the values read so far
    return (timeout, memory, runtime, memend, memmax, numsols, timesols, timelabels, memlabels)


# -----------------------------------------------------------------------------
# parsevaldepth0
#
# parses the contents of a VAL log file and retrieves its contents. If warning
# is specified, a warning is issued everytime a given line does not match a
# particular regexp. If the VAL log file does not exist then return no contents
# and exit silently
# -----------------------------------------------------------------------------
def parsevaldepth0 (directory, logfile, warning=False):

    """
    parses the contents of a VAL log file and retrieves its contents. If warning
    is specified, a warning is issued everytime a given line does not match a
    particular regexp. If the VAL log file does not exist then return no
    contents and exit silently
    """

    # check whether the logfile exists or not ---if it does not exist then
    # logfile shall be None
    if (not logfile):

        # if it does not exist then return default values
        return ('?', 0, [], [])

    # get the contents of the logfile (which is known to exist)
    logpathfile = directory + '/' + logfile
    logstream = open (logpathfile, 'r')
    lines = logstream.readlines ()

    # get the number of non-empty solution files and the number of correct
    # solutions found
    try:
        valnumsols = int (parsefield0 (VALNUMSOLS, 'valnumsols', lines, logpathfile, warning) [0])
        oknumsols = int (parsefield0 (OKNUMSOLS, 'oknumsols', lines, logpathfile, warning)[0])

    except:
        print """
 Fatal exception raised while getting one of the primitive VAL values
 Directory: %s
""" % logpathfile
        sys.exit ()

    # read the number of solution files and also the final value and the step
    # length of each solution
    if (oknumsols > 0):

        try:
            plansoln   = parsefield0 (PLANSOLN, 'plansoln', lines, logpathfile, warning)
            rawvalues  = [float (ivalue) 
                         for ivalue in parsefield0 (VALUE, 'value', lines, logpathfile, warning)]
            rawlengths = [int (ilength) 
                         for ilength in parsefield0 (LENGTH, 'length', lines, logpathfile, warning)]

            # now, it might be the case that some plans are correct whereas
            # others are not - filter the plans retaining only those which are
            # not -1
            values     = [ivalue for ivalue in rawvalues if ivalue != -1]
            lengths    = [ilength for ilength in rawlengths if ilength != -1]
            okplansoln = [iplansoln[1] for iplansoln in zip(rawvalues, plansoln)
                          if iplansoln[0] != -1]

        except Exception, message:
            print """
 Fatal exception raised while getting information from the solution files
 Directory: %s
""" % logpathfile
            sys.exit ()

    else:
        plansoln = okplansoln = values = lengths = list ()

    # close and exit
    logstream.close ()

    # and return the values read so far
    return (valnumsols, oknumsols, plansoln, okplansoln, values, lengths)


# -----------------------------------------------------------------------------
# depth0
#
# generates a report of the requested variables of a depth 0 directory, this is,
# a track-subtrack-planner-domain-problem. If warning is specified, a warning is
# issued everytime a given line does not match a particular regexp. The
# resulting table is named after "name"
# -----------------------------------------------------------------------------
def depth0 (directory, name, variables, unroll, warning = False):

    """
    generates a report of the requested variables of a depth 0 directory, this
    is, a track-subtrack-planner-domain-problem. If warning is specified, a
    warning is issued everytime a given line does not match a particular
    regexp. The resulting table is named after "name"
    """

    # first, check whether directory is depth 0 and retrieve info from it
    (logfile, vallogfile, planner, domain, problem) = checkdepth0 (directory)

    # now, parse its contents
    (timeout, memory, runtime, memend, memmax, numsols, timesols, timelabels, memlabels) = \
        parselogdepth0 (directory, logfile, warning)
    (valnumsols, oknumsols, plansoln, okplansoln, values, lengths) = \
                 parsevaldepth0 (directory, vallogfile, warning)

    # now, store all this information within a single instance of a run - note
    # that the level for reporting results is necessarily 0 here since levels
    # above depth are forbiddent (they make no sense) and it is not possible a
    # level below 0
    run = IPCrun.IPCrun (IPCrun.TRK_PLN_DMN_PRB, 0)
    run.set_unroll (unroll)
    run.set_name (name)

    # first fill in the information of raw parameters
    run [('',IPCrun.LOGFILE)]    = logfile
    run [('',IPCrun.VALLOGFILE)] = vallogfile
    run [('',IPCrun.PLANNER)]    = planner
    run [('',IPCrun.DOMAIN)]     = domain
    run [('',IPCrun.PROBLEM)]    = problem
    run [('',IPCrun.TIMEOUT)]    = timeout
    run [('',IPCrun.MEMBOUND)]   = memory / 1048576
    run [('',IPCrun.RUNTIME)]    = runtime
    run [('',IPCrun.MEMEND)]     = memend
    run [('',IPCrun.MEMMAX)]     = memmax
    run [('',IPCrun.NUMSOLS)]    = numsols
    run [('',IPCrun.VALNUMSOLS)] = valnumsols
    run [('',IPCrun.OKNUMSOLS)]  = oknumsols
    run [('',IPCrun.TIMESOLS)]   = timesols
    run [('',IPCrun.TIMELABELS)] = timelabels
    run [('',IPCrun.MEMLABELS)]  = memlabels
    if (numsols > 0):
        run [('', IPCrun.TIMEFIRSTSOL)] = timesols [0]
        run [('', IPCrun.TIMELASTSOL)]  = timesols [-1]
    else:
        run [('', IPCrun.TIMEFIRSTSOL)] = -1
        run [('', IPCrun.TIMELASTSOL)]  = -1
    run [('',IPCrun.SOLVED)]     = (valnumsols > 0)
    if (oknumsols == '?'):
        run [('',IPCrun.OKSOLVED)]   = '?'
    else:
        run [('',IPCrun.OKSOLVED)]   = (oknumsols > 0)
    run [('',IPCrun.PLANSOLN)]   = plansoln
    run [('',IPCrun.OKPLANSOLN)] = okplansoln
    run [('',IPCrun.VALUES)]     = values
    if (len (values) > 0):
        run [('',IPCrun.UPPERVALUE)] = max (values)
        run [('',IPCrun.LOWERVALUE)] = min (values)
    else:
        run [('',IPCrun.UPPERVALUE)] = 0 
        run [('',IPCrun.LOWERVALUE)] = 0
    run [('',IPCrun.LENGTHS)] = lengths
    if (len (lengths) > 0):
        run [('',IPCrun.MAXLENGTH)] = max (lengths)
        run [('',IPCrun.MINLENGTH)] = min (lengths)
    else:
        run [('',IPCrun.MAXLENGTH)] = 0 
        run [('',IPCrun.MINLENGTH)] = 0

    # compute the oktimesols raw variable which reports the elapsed time when
    # each valid solution file was generated. The process consists simply of
    # copying those positions from timesols that correspond to plan solution
    # files that were found to be valid by VAL
    oktimesols = [itimesol [1] for itimesol in zip (plansoln, timesols)
                                   if itimesol[0] in okplansoln]
    run[('',IPCrun.OKTIMESOLS)] = oktimesols
    if (oktimesols):
        run[('',IPCrun.OKTIMEFIRSTSOL)] = oktimesols [0]
        run[('',IPCrun.OKTIMELASTSOL)]  = oktimesols [-1]
    else:
        run[('',IPCrun.OKTIMEFIRSTSOL)] = -1
        run[('',IPCrun.OKTIMELASTSOL)]  = -1

    # now, initialize all the elaborated data
    run [('',IPCrun.SUMRUNTIME)]   = runtime
    run [('',IPCrun.MINRUNTIME)]   = runtime
    run [('',IPCrun.MAXRUNTIME)]   = runtime
    run [('',IPCrun.SUMMEMEND)]    = memend
    run [('',IPCrun.MINMEMEND)]    = memend
    run [('',IPCrun.MAXMEMEND)]    = memend
    run [('',IPCrun.SUMMEMMAX)]    = memmax
    run [('',IPCrun.MINMEMMAX)]    = memmax
    run [('',IPCrun.MAXMEMMAX)]    = memmax
    run [('',IPCrun.SUMNUMSOLS)]   = numsols
    run [('',IPCrun.OKSUMNUMSOLS)] = oknumsols
    run [('',IPCrun.NUMPROBS)]     = 1
    if (len (timesols) > 0):
        run [('',IPCrun.NUMSOLVED)]    = 1
        if (oknumsols == '?'):
            run [('',IPCrun.OKNUMSOLVED)]  = '?'
        else:
            run [('',IPCrun.OKNUMSOLVED)]  = {False: 0, True: 1}[(oknumsols>0)]
        run [('',IPCrun.NUMFAILS)]     = 0
        run [('',IPCrun.TIMEFAILS)]    = []
        run [('',IPCrun.MEMFAILS)]     = []
        run [('',IPCrun.UNEXFAILS)]    = []
        run [('',IPCrun.NUMTIMEFAILS)] = 0
        run [('',IPCrun.NUMMEMFAILS)]  = 0
        run [('',IPCrun.NUMUNEXFAILS)] = 0
    else:
        run [('',IPCrun.NUMSOLVED)]   = 0
        run [('',IPCrun.OKNUMSOLVED)] = 0
        run [('',IPCrun.OKNUMSOLVED)] = 0
        run [('',IPCrun.NUMFAILS)]    = 1

        # in the following, an attempt is made to try to characterize the
        # reason why a particular planner failed for a particular
        # problem. Note that the mem requirement is somehow relaxed (and a
        # giga is considered to be 1000 times instead of 1024 times
        # instead). This has to do with the margins used in
        # invoke-planner.run
        if (runtime >= timeout):
            run [('',IPCrun.TIMEFAILS)]    = [problem]
            run [('',IPCrun.MEMFAILS)]     = []
            run [('',IPCrun.UNEXFAILS)]    = []
            run [('',IPCrun.NUMTIMEFAILS)] = 1
            run [('',IPCrun.NUMMEMFAILS)]  = 0
            run [('',IPCrun.NUMUNEXFAILS)] = 0
        elif (memmax * 1048576 >= (1048576000 * memory/(1024*1048576))):
            run [('',IPCrun.TIMEFAILS)]    = []
            run [('',IPCrun.MEMFAILS)]     = [problem]
            run [('',IPCrun.UNEXFAILS)]    = []
            run [('',IPCrun.NUMTIMEFAILS)] = 0
            run [('',IPCrun.NUMMEMFAILS)]  = 1
            run [('',IPCrun.NUMUNEXFAILS)] = 0
        else:
            run [('',IPCrun.TIMEFAILS)]    = []
            run [('',IPCrun.MEMFAILS)]     = []
            run [('',IPCrun.UNEXFAILS)]    = [problem]
            run [('',IPCrun.NUMTIMEFAILS)] = 0
            run [('',IPCrun.NUMMEMFAILS)]  = 0
            run [('',IPCrun.NUMUNEXFAILS)] = 1

    # compute now the minimum and maximum value computed by VAL
    if (len (values) > 0):
        run [('',IPCrun.MINVALUE)] = min (values) 
        run [('',IPCrun.MAXVALUE)] = max (values)
    else:
        run [('',IPCrun.MINVALUE)] =  0
        run [('',IPCrun.MAXVALUE)] =  0      

    # finally, enable only the selected variables ---it might seem stupid to
    # compute them all and then to enable only a few to be shown but this is the
    # right choice since variables in the upper depths might need disabled
    # variables in this depth to compute their value
    map (lambda ivar:run.enable (eval ("IPCrun."+ivar.upper ())), variables)
            
    # and return the information retrieved so far
    return run



# Local Variables:
# mode:python
# fill-column:80
# End:
