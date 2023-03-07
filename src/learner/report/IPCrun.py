#!/usr/bin/python
#
# IPCrun.py
# Description: Information about a particular execution
# -----------------------------------------------------------------------------
#
# Started on  <Mon Apr 11 23:42:32 2011 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:09:39 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPCrun.py 321 2012-07-15 14:21:33Z clinares                          $
# $Date:: 2012-07-15 16:21:33 +0200 (dom 15 de jul de 2012)                 $
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
Information about a particular execution
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.3'
__revision__ = '$Revision: 321 $'

# formats recognized for printing 
NB_FORMATS = 5
TABLE, OCTAVE, HTML, EXCEL, WIKI = range (0, NB_FORMATS)

CHAR_SEP = '/'        # separator used to distinguished consecutive fields

# recognized levels of different sets of runs

# 0, for a particular run
# 1, for a number of executions of the same planner/domain,
# 2, for a number of executions in different domains of the same
#    planner,
# 3, for executions of an arbitrary collection of planners/domains
#    within the same track-subtrack
TRK_PLN_DMN_PRB, TRK_PLN_DMN, TRK_PLN, TRK = 0, 1, 2, 3

LEVELS = {
    TRK_PLN_DMN_PRB : "problem",
    TRK_PLN_DMN     : "domain",
    TRK_PLN         : "planner",
    TRK             : "track"}

# modes of display:

#   HOMOGENEOUS: means that all the variables requested are of the same type,
#                either raw or elaborated (see below). In this case, all
#                variables are necessarily shown at the same level (in case of
#                raw variables, at level 0, otherwise, as specified by the level
#                internal attribute)

#   HETEROGENEOUS: means that enable variables are both raw and elaborated. In
#                  this case, elaborated values are pushed down until level 0 so
#                  that all raw and elaborated data are shown in the same row
HOMOGENEOUS, HETEROGENEOUS = range (0,2)

# variables

# to add a new variable:

#   First, make sure it has an index assigned. If not, add it below
#   Second, add it in the VARS dictionary
#   Thirdly, provide a short description in the DESCS dictionary
#   Next, update the value of NUMVARS
#   Finally, provide handlers for the initialization and in case the new var is
#   elaborated also for the propagation and add of variables at the bottom of
#   this file

# Also, take into account that ELABORATEIDX is the index to the first elaborated
# index. If a raw variable is added, this variable shall be incremented

NUMVARS = 56
ELABORATEDIDX = 33
LOGFILE, VALLOGFILE, TRACK, SUBTRACK, PLANNER, DOMAIN, PROBLEM, \
TIMEOUT, MEMBOUND, RUNTIME, MEMEND, MEMMAX, NUMSOLS, VALNUMSOLS, OKNUMSOLS, TIMESOLS, OKTIMESOLS, \
TIMELABELS, MEMLABELS, TIMEFIRSTSOL, TIMELASTSOL, OKTIMEFIRSTSOL, OKTIMELASTSOL, SOLVED, OKSOLVED, \
PLANSOLN, OKPLANSOLN, VALUES, UPPERVALUE, LOWERVALUE, LENGTHS, MAXLENGTH, MINLENGTH, \
SUMRUNTIME, MINRUNTIME, MAXRUNTIME, SUMMEMEND, MINMEMEND, MAXMEMEND, SUMMEMMAX, MINMEMMAX, \
MAXMEMMAX, SUMNUMSOLS, OKSUMNUMSOLS, NUMPROBS, NUMSOLVED, OKNUMSOLVED, NUMFAILS, TIMEFAILS, \
 MEMFAILS, UNEXFAILS, NUMTIMEFAILS, NUMMEMFAILS, NUMUNEXFAILS, MINVALUE, MAXVALUE  = \
    range (0, NUMVARS)


VARS = {
    LOGFILE        : "logfile",             # raw data
    VALLOGFILE     : "vallogfile",
    TRACK          : "track",
    SUBTRACK       : "subtrack",
    PLANNER        : "planner",
    DOMAIN         : "domain",
    PROBLEM        : "problem",
    TIMEOUT        : "timeout",
    MEMBOUND       : "membound",
    RUNTIME        : "runtime",
    MEMEND         : "memend",
    MEMMAX         : "memmax",
    NUMSOLS        : "numsols",
    VALNUMSOLS     : "valnumsols",
    OKNUMSOLS      : "oknumsols",
    TIMESOLS       : "timesols",
    OKTIMESOLS     : "oktimesols",
    TIMELABELS     : "timelabels",
    MEMLABELS      : "memlabels",
    TIMEFIRSTSOL   : "timefirstsol",
    TIMELASTSOL    : "timelastsol",
    OKTIMEFIRSTSOL : "oktimefirstsol",
    OKTIMELASTSOL  : "oktimelastsol",
    SOLVED         : "solved",
    OKSOLVED       : "oksolved",
    PLANSOLN       : "plansoln",
    OKPLANSOLN     : "okplansoln",
    VALUES         : "values",
    UPPERVALUE     : "uppervalue",
    LOWERVALUE     : "lowervalue",
    LENGTHS        : "lengths",
    MAXLENGTH      : "maxlength",
    MINLENGTH      : "minlength",

    SUMRUNTIME     : "sumruntime",          # elaborated data
    MINRUNTIME     : "minruntime",
    MAXRUNTIME     : "maxruntime",
    SUMMEMEND      : "summemend",
    MINMEMEND      : "minmemend",
    MAXMEMEND      : "maxmemend",
    SUMMEMMAX      : "summemmax",
    MINMEMMAX      : "minmemmax",
    MAXMEMMAX      : "maxmemmax",
    SUMMEMEND      : "summemend",
    SUMNUMSOLS     : "sumnumsols",
    OKSUMNUMSOLS   : "oksumnumsols",
    NUMPROBS       : "numprobs",
    NUMSOLVED      : "numsolved",
    OKNUMSOLVED    : "oknumsolved",
    NUMFAILS       : "numfails",
    TIMEFAILS      : "timefails",
    MEMFAILS       : "memfails",
    UNEXFAILS      : "unexfails",
    NUMTIMEFAILS   : "numtimefails", 
    NUMMEMFAILS    : "nummemfails",
    NUMUNEXFAILS   : "numunexfails",
    MINVALUE       : "minvalue",
    MAXVALUE       : "maxvalue"}

DESCS = {
    LOGFILE        : "logfile with the information of a particular run",
    VALLOGFILE     : "VAL logfile with the information of a particular validation",
    TRACK          : "track of an arbitrary number of runs",
    SUBTRACK       : "subtrack of an arbitrary number of runs",
    PLANNER        : "planner used for solving an arbitrary number of problems",
    DOMAIN         : "domain of a particular number of runs",
    PROBLEM        : "problem identifier",
    TIMEOUT        : "time bound set during execution (in seconds)",
    MEMBOUND       : "memory bound set during execution (in MB)",
    RUNTIME        : "overall runtime (in seconds)",
    MEMEND         : "memory used by the planner when the problem was solved (in MB)",
    MEMMAX         : "maximum memory used, i.e. peaks considered (in MB)",
    NUMSOLS        : "total number of solution files generated",
    VALNUMSOLS     : "number of non-empty solution files generated",
    OKNUMSOLS      : "total number of *successful* solution files generated",
    TIMESOLS       : "elapsed time when each solution was generated (in seconds)",
    OKTIMESOLS     : "elapsed time when each *valid* solution was generated (in seconds)",
    TIMELABELS     : "time ticks used for sampling memory consumption (in seconds)",
    MEMLABELS      : "memory consumption at a particular time tick (in MB)",
    TIMEFIRSTSOL   : "time stamp of the first solution file (which might be empty!) or -1 if none",
    TIMELASTSOL    : "time stamp of the last solution file (which might be empty!) or -1 if none",
    OKTIMEFIRSTSOL : "time stamp of the first *valid* solution file or -1 if none",
    OKTIMELASTSOL  : "time stamp of the last *valid* solution file or -1 if none",
    SOLVED         : "whether a particular problem was solved or not",
    OKSOLVED       : "whether a particular problem was *successfully* solved or not",
    PLANSOLN       : "filenames of the solution files generated",
    OKPLANSOLN     : "filenames of valid solution files",
    VALUES         : "final values returned by VAL, one per each *valid* solution file",
    UPPERVALUE     : "largest value returned by VAL",
    LOWERVALUE     : "smallest value returned by VAL",
    LENGTHS        : "step length of all the plans validates by VAL, one per each *valid* solution file",
    MAXLENGTH      : "largest step length returned by VAL",
    MINLENGTH      : "smallest step length returned by VAL",

    SUMRUNTIME     : "sum of all the run times (in seconds)",
    MINRUNTIME     : "minimum run time (in seconds)",
    MAXRUNTIME     : "maximum run time (in seconds)",
    SUMMEMEND      : "sum of all the memory consumption at the end of the process, no peaks considered (in MB)",
    MINMEMEND      : "minimum of all the memory consumption at the end of the process, no peaks considered (in MB)",
    MAXMEMEND      : "maximum of all the memory consumption at the end of the process, no peaks considered (in MB)",
    SUMMEMMAX      : "sum of the maximum memory used, i.e., peaks considered (in MB)",
    MINMEMMAX      : "minimum of the maximum memory used, i.e., peaks considered (in MB)",
    MAXMEMMAX      : "maximum of the maximum memory used, i.e., peaks considered (in MB)",
    SUMNUMSOLS     : "sum of the total number of solution files generated",
    OKSUMNUMSOLS   : "sum of the total number of *successful* solution files generated",
    NUMPROBS       : "total number of problems",
    NUMSOLVED      : "number of solved problems (independently of the solution files generated)",
    OKNUMSOLVED    : "number of *successfully* solved problems (independently of the solution files generated)",
    NUMFAILS       : "total number of fails",
    TIMEFAILS      : "problem ids where the planner failed on time",
    MEMFAILS       : "problem ids where the planner failed on memory",
    UNEXFAILS      : "problem ids where the planner unexpectedly failed",
    NUMTIMEFAILS   : "number of time fails", 
    NUMMEMFAILS    : "number of mem fails",
    NUMUNEXFAILS   : "number of unexplained fails",
    MINVALUE       : "minimum cost returned by VAL",
    MAXVALUE       : "maximum cost returned by VAL"}


# this predicate returns True if var is elaborated and false otherwise
def iselaborated (var):
    """
    this predicate returns True if var is elaborated and false otherwise
    """

    return (var>=ELABORATEDIDX)


# the following service traverses recursively a given dictionary until the key
# (all items in K) is exhausted. Next, it creates an entry for the given
# variable with the specified value. If the dictionary does not contain the key
# as specified, the necessary subentries are created as well.
def _set (D, K, var, val):
    """
    the following service traverses recursively a given dictionary until the key
    (all items in K) is exhausted. Next, it creates an entry for the given
    variable with the specified value. If the dictionary does not contain the
    key as specified, the necessary subentries are created as well.
    """

    # base case - the key is empty
    if (len (K) == 0):

        # just add/modify the variable and return the resulting dictionary
        D [var] = val
        return D

    # general case - there are at least one key to traverse in the dictionary
    if (K[0] not in D.keys ()):

        # if the first key does not exist, then add it
        D [K[0]] = {}

    # and process now recursively the rest of the keys/value
    _set (D[K[0]], K[1:], var, val)

    # and finally return the resulting dictionary
    return D    


# the following service is equivalent to the previous one but instead of
# writing, it returns the value of the specified variable for the given K. If
# none exists, an exception is raised
def _get (D, K, var):
    """
    the following service is equivalent to the previous one but instead of
    writing, it returns the value of the specified variable for the given K. If
    none exists, an exception is raised
    """

    # base case - there are no more keys to traverse in D
    if (len (K) == 0):

        # just return the requested value
        if (var in D.keys ()):
            return D[var]
        else:
            raise KeyError, " The requested variable '%s' has not been found" % (VARS [var])

    # general case - there are still more keys to traverse
    if (K[0] in D.keys ()):

        # progress recursively
        return _get (D[K[0]], K[1:], var)

    else:
        raise KeyError, " Unknown key '%s'" % K[0]


# return the children of the dictionary D that are present at the specified
# depth. A key is said to be a children if it contains another dictionary. The
# children at the specified depth are all merged if a positive depth is provided
def _children (D, depth=0):
    """
    return the children of the dictionary D that are present at the root. A key
    is said to be a children if it contains another dictionary
    """

    # case base - depth=0
    if (depth == 0):
        return [item[0] for item in filter (lambda x:type (x[1])==dict, D.items ())]

    # general case - return the merge of all the children computed at the next
    # level
    return sorted (list (reduce (lambda x,y:set(x).union (set(y)), 
                                 [_children (D [ikey], depth-1) for ikey in _children (D, 0)])))


# return all the keys of the dictionary D that are stored at the given depth. If
# keys beneath the root of the dictionary are requested, the keys are computed
# as the merge of the keys at that level in all branches
def _keys (D, depth=0):
    """
    return all the keys of the dictionary D that are stored at the given
    depth. If keys beneath the root of the dictionary are requested, the keys
    are computed as the merge of the keys at that level in all branches
    """

    # case base - depth=0
    if (depth == 0):
        return D.keys ()

    # general case - return the merge of all the children computed at the next
    # level
    return sorted (list (reduce (lambda x,y:set(x).union (set(y)), 
                                 [_keys (D [ikey], depth-1) for ikey in _children (D,0)])))


# return a list of tuples (key, value) with the contents of the specified
# dictionary D, where value might be another nested list with other tuples
# (key,value) as well
def _items (D):
    """
    return a list of tuples (key, value) with the contents of the specified
    dictionary D, where value might be another nested list with other tuples
    (key,value) as well
    """

    # initialization
    result = list ()
    
    # base case - the dictionary is empty
    if (len (D) != 0):

        # general case - the dictionary ain't empty
        for (key, value) in D.items ():

            # in case this key does not point to a new dictionary, just add its
            # value
            if (type (value) != dict):

                result.append ((key, value))

            # otherwise, compute the list of (key,value) of its descendant and
            # add them to this list of items
            else:

                child = _items (value)
                result.append ((key, child))

    # finally, exit with the list of items computed so far
    return result


# filter the contents of the specified dictionary (which has the specified
# depth) removing all the subdicts whose key does not meet the corresponding
# regexps. The regular expressions are given as a dictionary that specify, at
# each level, the regular expressions to be satisfied at that level
def _filter (D, R, depth):
    """
    filter the contents of the specified dictionary (which has the specified
    depth) removing all the subdicts whose key does not meet the corresponding
    regexps. The regular expressions are given as a dictionary that specify, at
    each level, the regular expressions to be satisfied at that level
    """

    # for every entry to another subdict
    for ichild in _children (D, 0):

        # if this does not meet the given regexp
        if (not re.match (R[depth], ichild)):

            # delete it
            del D[ichild]

        # if it does, 
        else:

            # preserve it and filter the contents of its dictionary
            _filter (D[ichild], R, depth-1)


# the procedure of unrolling is exactly equal to the notion of "zipping" in
# Python ---and all functional languages. Given an arbitrary number of lists
# (stored in 'rest'), N lists are created (with N the length of the shortest
# list in 'rest') whose ith component is the list with the items in the ith
# position of all lists in 'rest'
#
# 'header' is used only to qualify every resulting list with the same items
def _unroll (header, *rest):
    """
    the procedure of unrolling is exactly equal to the notion of"zipping" in
    Python ---and all functional languages. Given an arbitrary number of lists
    (stored in 'rest'), N lists are created (with N the length of the shortest
    list in 'rest') whose ith component is the list with the items in the ith
    position of all lists in 'rest'
    
    'header' is used only to qualify every resulting list with the same items
    """

    # initialization
    lst = list ()

    # Compute the N lists that result from "zipping" all the specified
    # lists and qualify each one with the given header
    for iline in zip (*rest):

        lst.append (header + list (iline))

    # finally, return the lines computed this way
    return lst
    

# list the values of all variables in V stored at the requested level in the
# specified dictionary generated at the given depth ---all entries in the output
# string are qualified with their key K
#
# mode is one of the values HOMOGENEOUS/HETEROGENEOUS. In the first mode, all
# enabled variables are of the same type so that they are printed out at the
# same level (0 if they are raw and the specified level otherwise). If the mode
# is heterogeneous, then elaborated data is pushed down the tree in E until
# level 0 so that they are shown together with raw data
#
# if 'unroll' is requested then each value is shown multiple times, once per
# each entry. This makes sense if variables contain vectors and it is desired to
# show a match between an arbitrary number of vectors, each final line with
# values that are located in the same position in each vector
def _print (D, V, depth, level, mode, K=[], E={}, unroll=False):
    """
    list the values of all variables in V stored at the requested level in the
    specified dictionary generated at the given depth ---all entries in the
    output string are qualified with their key K
    
    mode is one of the values HOMOGENEOUS/HETEROGENEOUS. In the first mode, all
    enabled variables are of the same type so that they are printed out at the
    same level (0 if they are raw and the specified level otherwise). If the
    mode is heterogeneous, then elaborated data is pushed down the tree in E
    until level 0 so that they are shown together with raw data

    if 'unroll' is requested then each value is shown multiple times, once per
    each entry. This makes sense if variables contain vectors and it is desired
    to show a match between an arbitrary number of vectors, each final line with
    values that are located in the same position in each vector
    """

    # this method simply traverses the private dictionary in breadth-first order
    # and prints out the values of all the enabled variables found at all levels
    # until the dictionary is exhausted ---variables are printed out in the same
    # order they are specified in V
    lst = list ()

    # values are shown only if we are at the requested level or if variables in
    # V are raw

    # create a row to be printed out just by inspecting the entry points at D
    # and adding new fields if those specified in V are present here
    line = list ()
    for ivar in V:
        if (((ivar < ELABORATEDIDX) or
             ((ivar>=ELABORATEDIDX) and (depth==level) and (mode==HOMOGENEOUS))) and
            ivar in D.keys ()):
            line.append (D[ivar])

        if ((ivar >=ELABORATEDIDX) and (depth==0) and (mode==HETEROGENEOUS) and
            ivar in E.keys ()):
            line.append (E[ivar])

    # qualify the line with the key prefix and add it to the string to return in
    # case there are some values to print out
    if (len (line) > 0):
        header = list ()
        for ikey in K:
            header.append (ikey)

        # in case that it was requested to unroll lines
        if (unroll):

            # then compute the new list of lines and just add them to the
            # partial collection computed so far
            lst += _unroll (header, *line)

        # otherwise, there is no need to make any further computation and add
        # this single line to the partial collection of lines to show in the
        # output
        else:
            lst.append (header + line)

    # now, go on to the next level printing other variables that might be stored at
    # the children of this dictionary
    for ikey in sorted (D.keys ()):

        # if there are any elaborated data at this level that has to be pushed
        # down, add it to an ancilliary dictionary to pass it by in the next
        # recursive call
        elaborated = E
        for ivar in V:
            if ((ivar>=ELABORATEDIDX) and (depth==level) and (mode==HETEROGENEOUS) and
                ivar in D.keys ()):
                elaborated [ivar] = D [ivar]

        # in case this key is an entry point to another dict
        if (type (D[ikey]) == dict):

            lst += _print (D[ikey], V, depth-1, level, mode, K + [ikey], elaborated, unroll)

    # finally, return the resulting list
    return lst


# lexicographicalcm is a multi-cmp that takes two lists x and y and compares
# them in lexicographical order according to the sorting schema. It returns -1
# if x < y, 0 if x=y and 1 otherwise. The schema consists of a list of pairs
# (record, <|>) where record is a position of both x and y and < indicates that
# ascending orders shall be checked whereas > indicates quite the opposite
def _lexicographicalcmp (x, y, sorting):
    """
    lexicographicalcm is a multi-cmp that takes two lists x and y and compares
    them in lexicographical order according to the sorting schema. It returns -1
    if x < y, 0 if x=y and 1 otherwise. The schema consists of a list of pairs
    (record, <|>) where record is a position of both x and y and < indicates
    that ascending orders shall be checked whereas > indicates quite the
    opposite
    """

    result = 0                          # both x and y are equal by default

    # for each criteria and while it is undecided whether one instance is
    # greater/less than the other
    while (not result and len (sorting)>0):
        criteria = {False: -1, True: +1} [sorting [0][1] == '<']
        result = criteria * cmp (x[sorting[0][0]], y[sorting[0][0]])
        sorting = sorting [1:]

    # and return the result so far
    return result


# the following service sorts all the items in L (which is a list of lists, each
# one being a line which consists of many lists as records in the same line)
# according to the given sorting schema (specified as a list [(key/var, <|>)]
# where < stands for ascending order and > for descending order). The parameters
# enabled, depth, level and mode are used for identifying useful keys in the
# sorting schema ---if some are requested which are not used in L they are just
# ignored
def _sort (L, sorting, enabled, depth, level, mode):
    """
    the following service sorts all the items in L (which is a list of lists,
    each one being a line which consists of many lists as records in the same
    line) according to the given sorting schema (specified as a list [(key/var,
    <|>)] where < stands for ascending order and > for descending order). The
    parameters enabled, depth, level and mode are used for identifying useful
    keys in the sorting schema ---if some are requested which are not used in L
    they are just ignored
    """

    keys = ['problem', 'domain', 'planner', 'track']

    # now, compute the right positions in L that have to be compared according
    # to the sorting schema. Take into account that these might be either keys
    # or variables
    schema = list ()
    key0, key1 = depth-1, \
        {False: 0, True: level} [mode == HOMOGENEOUS and enabled [0]>=ELABORATEDIDX]
    for isorting in sorting:

        # compute the right column to look at for applying this sorting criteria
        if (isorting[0] in keys):               # sort by key
            index = keys.index (isorting [0])
            if (index <= key0 and index >= key1):
                schema.append ( (key0 - index, isorting [1]) )

        else:                                   # sort by variable
            schema.append ( (key0 - key1 + 1 + enabled.index (eval(isorting [0].upper ())), 
                             isorting [1]) )

    # now, sort all items in lexicographical order according to the sorting
    # schema just computed
    if (len (schema)>0):

        L = sorted (L, cmp=lambda x, y:_lexicographicalcmp (x, y, schema))

    # now, return the sorted list
    return L


# imports
# -----------------------------------------------------------------------------
import copy                             # deep copies of dictionaries and lists
import datetime                         # for printing current date and time
import getpass                          # to retrieve the username
import pickle
import re                               # regular expressions
import socket                           # to find out the computer's name

import pyExcelerator.Workbook           # excel workbooks
import pyExcelerator.Style              # excel styles
import PrettyTable                      # for creating pretty tables

# -----------------------------------------------------------------------------
# IPCrun
#
#     This class keeps information about a particular set of variables
#     sampled during an arbitrary number of executions
# -----------------------------------------------------------------------------
class IPCrun:
    """
    This class keeps information about a particular set of variables
    sampled during an arbitrary number of executions
    """

    # default constructor
    def __init__ (self, depth=0, level=0):
        """
        default constructor
        """

        # first, simply initialize the private attributes of this class, namely
        # the depth of the execution, the (head) level used for reporting the
        # results and an empty dictionary
        self._depth = depth
        self._level = level
        self._vars = dict ()

        # and disable all keys by default ---incidentally, all enabled variables
        # are assumed to be of the same type (either raw or
        # elaborated). Besides, there is no sorting by default and the mode is
        # homogeneous (i.e, all the required variables are of the same type
        # ---either raw or elaborated)
        self._enabled = list ()
        self._mode = HOMOGENEOUS
        self._sorting = list ()

        # by default, set the table format
        self._format = TABLE

        # and avoid unrolling values ---i.e., show the values of all variables
        # as they've been collected instead of creating an arbitrary number of
        # rows that matches the contents from the same positions of different
        # vectors
        self._unroll = False

        # finally, initialize all the elaborated variables
        for ivariable in range (ELABORATEDIDX, NUMVARS):
            init_handler = "_init_%s ()" % VARS[ivariable].lower ()
            self._vars [ivariable] = eval ( init_handler )

        # make this IPCrun unnamed
        self._name = 'unnamed'

        # and store its version number to check serializations/deserializations
        self._revision = '$Revision: 321 $'


    # operator overloading

    # assignment operator - it attachs a value to a given index. An index is a
    # tuple of the form (key, variable) where a key is a string that can be
    # decomposed in a various subkeys separated by CHAR_SEP
    def __setitem__ (self, index, value):
        """
        assignment operator - it attachs a value to a given index. An index is a
        tuple of the form (key, variable) where a key is a string that can be
        decomposed in a various subkeys separated by CHAR_SEP
        """

        # first, check the index is a tuple with two items, the first being a
        # string and the second being a known variable
        if (type (index) != tuple or len (index) != 2):
            raise KeyError, " The index '%s' shall be a tuple with a string and a known variable" % index

        if (type (index[0]) != str):
            raise KeyError, " The key '%s' is not a string" % index [0]

        if (index[1] not in VARS):
            raise KeyError, " The specified variable '%i' is not known" % index[1]

        # insert the key in the private dictionary accordingly so that variables
        # are distinguished by their key
        if (index [0] == ''):
            _set (self._vars, [], index[1], value)
        else:
            _set (self._vars, index[0].split (CHAR_SEP), index[1], value)


    # accessor - it returns the value of the specified (key, var) in index
    def __getitem__ (self, index):
        """
        accessor - it returns the value of the specified (key, var) in index
        """

        # first, check the index is a tuple with two items, the first being a
        # string and the second being a known variable
        if (type (index) != tuple or len (index) != 2):
            raise KeyError, " The index '%s' shall be a tuple with a string and a known variable" % index

        if (type (index[0]) != str):
            raise KeyError, " The key '%s' is not a string" % index [0]

        if (index[1] not in VARS):
            raise KeyError, " The specified variable '%i' is not known" % index[1]

        # now, traverse the private dictionary according to the given key and
        # retrieve the specified value
        if (index [0] == ''):
            return _get (self._vars, [], index[1])
        else:
            return _get (self._vars, index[0].split (CHAR_SEP), index[1])


    # add two runs of the same depth by creating a new one which contains all
    # the information stored in both instances
    def __iadd__ (self, other):
        """
        add two runs of the same depth by creating a new one which contains all
        the information stored in both instances
        """

        # Check that both instances contain variables and values at the same
        # level
        if (self._depth != other._depth):
            raise ValueError, " It is not feasible to add two IPCrun at different depths"

        # now, copy all the contents of the other dictionary into this one but
        # avoiding two overwrite the elaborated variables which are considered
        # later on
        for ikey in other._vars.keys ():

            # thus, copy only children of this level
            if (type (other._vars [ikey]) == dict):
                self._vars [ikey] = copy.deepcopy (other._vars [ikey])

        # now, compute the values of all the elaborated variables from both
        # instances
        for ivariable in range (ELABORATEDIDX, NUMVARS):
            add_handler = "_add_%s (self[('',%i)], other[('',%i)])" % (VARS[ivariable].lower (), 
                                                                       ivariable, ivariable)
            self [('',ivariable)] = eval ( add_handler )

        # also, update the _enabled variables to be the union of the _enabled
        # lists of both instances but preserving their order
        for ivar in other._enabled:
            if (ivar not in self._enabled):
                self._enabled.append (ivar)

        # and the sorting schema and unroll flag are preserved

        # finally leave the level of this instance untouched and return the
        # contents of this new instance
        return self


    # printing service
    def __str__ (self):
        """
        printing service
        """

        # check there are some values to print
        if (len (self._enabled) == 0):
            return " Warning - All variables are disabled: empty report"

        # compute the mode of this IPCrun
        for ivar in self._enabled[1:]:
            if ( (self._enabled [0] <  ELABORATEDIDX and ivar >= ELABORATEDIDX) or 
                 (self._enabled [0] >= ELABORATEDIDX and ivar <  ELABORATEDIDX) ):
                self._mode = HETEROGENEOUS
                break

        # and now invoke the right service
        if (self._format == TABLE):
            return self.print_table ()
        
        elif (self._format == OCTAVE):
            return self.print_octave ()
        
        elif (self._format == HTML):
            return self.print_table ()

        elif (self._format == EXCEL):
            return self.print_excel ()

        elif (self._format == WIKI):
            return self.print_wiki ()


    # methods

    # return a list with all the keys found in the private dictionary of this
    # run at a given level that store other dictionaries. If the level specified
    # is beneath is below the current depth of this run, the keys returned
    # result of merging the children in all branches
    def children (self, level):
        """
        return a list with all the keys found in the private dictionary of this
        run at a given level that store other dictionaries. If the level
        specified is beneath is below the current depth of this run, the keys
        returned result of merging the children in all branches
        """

        # first, check that this dictionary contains keys at the specified level
        if (self._depth < level):

            # if it does not, just return an empty list
            return list ()

        # otherwise, this dictionary is known to contain the requested keys but
        # maybe they are located at the root or beneath this level
        return sorted (_children (self._vars, depth=self._depth - level))


    # return a list with all the keys found in the private dictionary of this
    # run at a given level. If the level specified is beneath the current depth
    # of this run, the keys returned result of merging the children in all
    # branches
    def keys (self, level):
        """
        return a list with all the keys found in the private dictionary of this
        run at a given level. If the level specified is beneath the current
        depth of this run, the keys returned result of merging the children in
        all branches
        """

        # first, check that this dictionary contains keys at the specified level
        if (self._depth < level):

            # if it does not, just return an empty list
            return list ()

        # otherwise, this dictionary is known to contain the requested keys but
        # maybe they are located at the root or beneath this level
        return sorted (_keys (self._vars, depth=self._depth - level))


    # return a list with tuples (key, value) from the contents of the private
    # dictionary, where value might be another list of tuples
    def items (self, level):
        """
        return a list with tuples (key, value) from the contents of the private
        dictionary, where value might be another list of tuples
        """

        return _items (self._vars)
        

    # returns True if the private dictionary stored in this run contains they
    # key k at the specified level
    def has_key (self, key, level):
        """
        returns True if the private dictionary stored in this run contains they
        key k at the specified level
        """

        return key in self.keys (level)


    # the following service removes all children whose key does not meet the
    # given regexp. The regular expressions are specified as a dictionary that
    # contains, for every level, a regular expression that has to be satisifed
    # by the (non-variable) keys of the same level
    #
    # This method does not update the values of elaborated variables when
    # removing some children!
    def filter (self, regexp):
        """
        the following service removes all children whose key does not meet the
        given regexp. The regular expressions are specified as a dictionary that
        contains, for every level, a regular expression that has to be satisifed
        by the (non-variable) keys of the same level
        
        This method does not update the values of elaborated variables when
        removing some children!
        """

        _filter (self._vars, regexp, self._depth)
    

    # returns a new instance whose private dictionary contains a *single* key
    # which stores the private dict of this instance
    def prefix (self, key):
        """
        returns a new instance whose private dictionary contains a *single* key
        which stores the private dict of this instance
        """

        # create a new instance whose depth has been incremented by one
        new = IPCrun (self._depth + 1, self._level)

        # create a dictionary with a single key which contains the other
        # dictionary.
        new._vars = {key:{}}
        for ikey in self._vars.keys ():

            new._vars [key][ikey] = copy.deepcopy (self._vars [ikey])

        # and now copy the other attributes
        new._enabled = copy.deepcopy (self._enabled)
        new._unroll = self._unroll
        new._sorting = self._sorting
        new._format = self._format

        # write all the elaborated data into this instance at the next level
        # created by this method
        for ivariable in range (ELABORATEDIDX, NUMVARS):
            prop_handler = "_propagate_%s (key, self._vars [%i])" % (VARS[ivariable].lower (),ivariable)
            new [('',ivariable)] = eval ( prop_handler )

        # and return the new instance
        return new


    # set the level of this run
    def set_level (self, level):
        """
        set the level of this run
        """
        
        self._level = level
        

    # sets the sorting schema which is a list of pairs (key/param, <|>) where
    # '<' stands for ascending and '>' stands for descending
    def set_sorting (self, schema):
        """
        sets the sorting schema which is a list of pairs (key/param, <|>) where
        '<' stands for ascending and '>' stands for descending
        """

        self._sorting = schema


    # sets a name for this IPCrun
    def set_name (self, name):
        """
        sets a name for this IPCrun
        """

        self._name = name


    # disables a variable to be shown 
    def disable (self, var):
        """
        disables a variable to be shown 
        """

        # try to remove the given value
        try:
            self._enabled.remove (var)

        # and if it was not there before, do nothing
        except:
            pass


    # disables all variables
    def disable_all (self):
        """
        disables all variables
        """

        self._enabled = []


    # enables a variable to be shown 
    def enable (self, var):
        """
        enables a variable to be shown 
        """

        self._enabled.append (var)


    # set the printing format
    def set_format (self, format):
        """
        set the printing format
        """
        
        if (format not in range (0, NB_FORMATS)):
            print """
 Error - Unrecognized format style %i""" % format
            raise ValueError

        self._format = format


    # set whether this run shall show the values of iterable contents unrolled
    # or not
    def set_unroll (self, unroll):
        """
        set whether this run shall show the values of iterable contents unrolled
        or not
        """

        self._unroll = unroll
        
        
    # the following service retrieves the contents that corresponds to the
    # selection criteria and sorts them accordingly
    def tablify (self):
        """
        the following service retrieves the contents that corresponds to the
        selection criteria and sorts them accordingly
        """

        # get the contents 
        contents = _print (self._vars, self._enabled, self._depth, self._level, 
                           self._mode, unroll=self._unroll)

        # sort the contents according to the sorting schema and return them
        return _sort (contents, self._sorting, self._enabled, self._depth, 
                      self._level, self._mode)


    # the following service prints the information of this class in octave
    # format
    def print_octave (self):
        """
        the following service prints the information of this class in octave
        format
        """

        # get the contents 
        contents = self.tablify ()

        # compute the keys used for representing these contents
        key0, key1 = self._depth, \
            {False: 0, True: self._level} [self._mode == HOMOGENEOUS and self._enabled [0]>=ELABORATEDIDX]

        # compute the header
        str = "# created by IPCrun %s (%s), %s\n" % (__version__, __revision__ [1:-2],
                                                     datetime.datetime.now ().strftime ("%c"))
        str += "# name: %s\n" % self._name
        str += "# type: matrix\n"
        str += "# rows: %i\n" % len (contents)
        str += "# columns: %i\n" % (key0-key1+len (self._enabled))

        # create the lines with the requested data
        for irow in contents:
            for ifield in irow:
                str += "%s " % ifield
            str += '\n'

        # compute the footer
        str += "# legend:\n"
        for ikey in range (key0-1, key1-1, -1):
            str += "#   %s [key]\n" % {TRK_PLN_DMN_PRB : 'problem', 
                                       TRK_PLN_DMN : 'domain',
                                       TRK_PLN : 'planner',
                                       TRK: 'track'} [ikey]
        for ivar in self._enabled:
            str += "#   %s: %s [%s]\n" % (VARS [ivar], DESCS [ivar],
                                          {False: "elaborated data", True: "raw data"}[ivar < ELABORATEDIDX])

        # return the whole string
        return str
    
    
    # print the contents of this class as a pretty table
    def print_table (self):
        """
        print the contents of this class as a pretty table
        """

        # get the contents
        contents = self.tablify ()

        # compute the keys used for representing these contents
        key0, key1 = self._depth, \
            {False: 0, True: self._level} [self._mode == HOMOGENEOUS and self._enabled [0]>=ELABORATEDIDX]

        # compute the headers of the table - first get the keys that result from
        # the difference between depth and level and next the variables
        headers = []
        for ikey in range (key0-1, key1-1, -1):
            headers.append ("%s" % {TRK_PLN_DMN_PRB : 'problem', 
                                    TRK_PLN_DMN : 'domain',
                                    TRK_PLN : 'planner',
                                    TRK: 'track'} [ikey])

        for ivar in self._enabled:
            headers.append (VARS [ivar])

        # create a pretty table
        table = PrettyTable.PrettyTable (headers)

        # now, start adding data rows
        for irow in contents:
            table.add_row (irow)

        # now, according to the style
        if (self._format ==  TABLE):
            table.set_style (PrettyTable.DEFAULT)
            sout = (" name: %s\n" % self._name) + table.get_string ()
        elif (self._format == HTML):
            sout = "<h1>name: %s</h1>\n%s" % (self._name, table.get_html_string ())

        # show the legend
        newline={False:"<br>", True: '\n'}[self._format==TABLE]
        boldopen={False:"<b>", True: ''}[self._format==TABLE]
        boldclose={False:"</b>", True: ''}[self._format==TABLE]
        emphasizeopen={False:"<em>", True: ''}[self._format==TABLE]
        emphasizeclose={False:"</em>", True: ''}[self._format==TABLE]

        if (self._format==TABLE):
            sout += newline + " legend:" + newline
        else:
            sout += "<h2>legend</h2>"
        for ikey in range (key0-1, key1-1, -1):
            sout += "   %s%s%s [key]" % (boldopen,
                                         {TRK_PLN_DMN_PRB : 'problem', 
                                          TRK_PLN_DMN : 'domain',
                                          TRK_PLN : 'planner',
                                          TRK: 'track'} [ikey],
                                         boldclose)
            sout += newline

        for ivar in self._enabled:
            sout += "   %s%s%s: %s [%s]" % (boldopen,VARS [ivar], boldclose, DESCS [ivar],
                                            {False: "elaborated data", True: "raw data"}[ivar < ELABORATEDIDX])
            sout += newline

        # and finally show the footer
        sout += newline
        sout += " %screated by IPCrun %s (%s), %s%s" % (emphasizeopen,
                                                        __version__, __revision__ [1:-2],
                                                        datetime.datetime.now ().strftime ("%c"),
                                                        emphasizeclose)
        sout += newline
        

        # return the table along with its name
        return sout


    # print the contents of this class in an excel file
    def print_excel (self):
        """
        print the contents of this class in an excel file
        """

        # get the contents 
        contents = self.tablify ()

        # compute the keys used for representing these contents
        key0, key1 = self._depth, \
            {False: 0, True: self._level} [self._mode == HOMOGENEOUS and self._enabled [0]>=ELABORATEDIDX]

        # create the excel page
        style = pyExcelerator.Style.XFStyle ()
        wb = pyExcelerator.Workbook ()
        ws = wb.add_sheet ("%s" % self._name)

        # create the styles

        # for the header
        hstyle = pyExcelerator.XFStyle ()
        hstyle.font.name = "Arial"
        hstyle.font.bold = True

        # for keys
        kstyle = pyExcelerator.XFStyle ()
        kstyle.font.name = "Arial"
        kstyle.font.bold = True
        kstyle.font.colour_index = 0x10             # dark red

        # for data
        dstyle = pyExcelerator.XFStyle ()
        dstyle.font.name = "Arial"
        dstyle.font.bold = False
        dstyle.font.colour_index = 0x27              # dark blue

        filename = "report.xls"

        # create the panes splitters
        ws.panes_frozen = True
        ws.horz_split_pos = 2
        ws.vert_split_pos = 1 + key0 - key1

        # compute the headers - first get the keys that result from the
        # difference between depth and level and next the variables
        row=col=1
        for ikey in range (key0-1, key1-1, -1):
            ws.write (row, col, "%s" % {TRK_PLN_DMN_PRB : 'problem', 
                                        TRK_PLN_DMN : 'domain',
                                        TRK_PLN : 'planner',
                                        TRK: 'track'} [ikey],
                      hstyle)
            col += 1

        for ivar in self._enabled:
            ws.write (row, col, VARS [ivar], hstyle)
            col += 1

        # now, start adding data rows
        row += 1
        col = 1
        for iline in contents:
            for icol in range (0, len (iline)):
                icontent = {False: iline [icol],True: str (iline [icol])[1:-1]}[type (iline [icol]) == list]
                if (icol < key0 - key1):
                    ws.write (row, col, icontent, kstyle)
                else:
                    ws.write (row, col, icontent, dstyle)
                col += 1
            row += 1
            col = 1

        # show the legend
        row += 2
        col = 1
        ws.write (row, col, "legend:")
        row += 1
        col = 1
        for ikey in range (key0-1, key1-1, -1):
            ws.write (row, col, "%s" % ({TRK_PLN_DMN_PRB : 'problem', 
                                         TRK_PLN_DMN : 'domain',
                                         TRK_PLN : 'planner',
                                         TRK: 'track'} [ikey]))
            ws.write (row, col+1,"[key]")
            row += 1

        for ivar in self._enabled:
            ws.write (row, col, "%s: %s" % (VARS [ivar], DESCS [ivar]))
            ws.write (row, col+1, "[%s]" % {False: "elaborated data", True: "raw data"}[ivar < ELABORATEDIDX])
            row += 1

        # and finally show the footer
        row += 1
        col = 1
        ws.write (row, col, " created by IPCrun %s (%s), %s" % (__version__, __revision__ [1:-2],
                                                                datetime.datetime.now ().strftime ("%c")))

        # save the excel page
        wb.save (filename)

        return ("Excel file '%s' generated" % filename)
        

    # print the contents of this class in the wiki markup language
    def print_wiki (self):
        """
        print the contents of this class in the wiki markup language
        """

        # get the contents 
        contents = self.tablify ()

        # compute the keys used for representing these contents
        key0, key1 = self._depth, \
            {False: 0, True: self._level} [self._mode == HOMOGENEOUS and self._enabled [0]>=ELABORATEDIDX]
        # print out the name of the table
        sout = "name: %s" % self._name

        # compute the headers - first get the keys that result from the
        # difference between depth and level and next the variables
        sout += "\n||"
        for ikey in range (key0-1, key1-1, -1):
            sout += " %s ||" % {TRK_PLN_DMN_PRB : 'problem', 
                                TRK_PLN_DMN : 'domain',
                                TRK_PLN : 'planner',
                                TRK: 'track'} [ikey]

        for ivar in self._enabled:
            sout += " %s ||" % VARS [ivar]

        # now, start adding data rows
        for iline in contents:
            sout += '\n||'
            for icontent in iline:
                sout += "  %s ||" % icontent

        # show the legend
        sout += "\nlegend:"
        for ikey in range (key0-1, key1-1, -1):
            sout += "\n  .  %s: [key]" % {TRK_PLN_DMN_PRB : 'problem', 
                                        TRK_PLN_DMN : 'domain',
                                        TRK_PLN : 'planner',
                                        TRK: 'track'} [ikey]

        for ivar in self._enabled:
            sout += "\n  .  %s: %s" % (VARS [ivar], DESCS [ivar])
            sout += " [%s]" % {False: "elaborated data", True: "raw data"}[ivar < ELABORATEDIDX]

        # and finally show the footer
        sout += "\n''created by IPCrun %s (%s), %s''" % (__version__, __revision__ [1:-2], 
                                                         datetime.datetime.now ().strftime ("%c"))

        # and return the string computed so far
        return sout


    # writes a pickled representation of this instance to the specified file
    def serialize (self, filename):
        """
        writes a pickled representation of this instance to the specified file
        """
        
        # open the file in write mode
        file = open (filename, 'wb')

        # pickles this object
        pickle.dump (self._depth, file, -1)
        pickle.dump (self._level, file, -1)
        pickle.dump (self._enabled, file, -1)
        pickle.dump (self._mode, file, -1)
        pickle.dump (self._sorting, file, -1)
        pickle.dump (self._format, file, -1)
        pickle.dump (self._name, file, -1)
        pickle.dump (self._revision, file, -1)
        pickle.dump (self._unroll, file, -1)
        pickle.dump (self._vars, file, -1)

        # and close the file
        file.close ()


    # reads a pickled representation from the given file to recreate the
    # contents of the original IPCrun
    def deserialize (self, filename):
        """
        reads a pickled representation from the given file to recreate the
        contents of the original IPCrun
        """

        # open the file
        file = open (filename, 'rb')

        # unpickles the data stream
        self._depth = pickle.load (file)
        self._level = pickle.load (file)
        self._enabled = pickle.load (file)
        self._mode = pickle.load (file)
        self._sorting = pickle.load (file)
        self._format = pickle.load (file)
        self._name = pickle.load (file)
        filerevision = pickle.load (file)
        self._unroll = pickle.load (file)
        self._vars = pickle.load (file)

        # and close the file
        file.close ()

        # check the revision from the snapshot, in case it is not the same than
        # the revision string of this instance, issue a warning
        if (filerevision != self._revision):

            print """
 Warning - The snapshot '%s' 
           has revision string '%s' that differs from the current one '%s'
           It is highly recommended either to use IPCrun revision '%s' or to recreate this
           snapshot. Otherwise, results are unpredictable!
""" % (filename, filerevision, self._revision, filerevision)

    
# handlers for handling elaborated data
# -----------------------------------------------------------------------------

# initialization

# for each elaborated var add a function _init_%var% () which just return the
# initial value in empty IPCruns

def _init_logfile ():
    return ''

def _init_vallogfile ():
    return ''

def _init_track ():
    return ''

def _init_subtrack ():
    return ''

def _init_planner ():
    return ''

def _init_domain ():
    return ''

def _init_problem ():
    return ''

def _init_timeout ():
    return 0

def _init_membound ():
    return 0

def _init_runtime ():
    return 0

def _init_memend ():
    return 0

def _init_memmax ():
    return 0

def _init_numsols ():
    return 0

def _init_valnumsols ():
    return 0

def _init_oknumsols ():
    return 0

def _init_timesols ():
    return []

def _init_oktimesols ():
    return []

def _init_timelabels ():
    return []

def _init_memlabels ():
    return []

def _init_timefirstsol ():
    return 0

def _init_timelastsol ():
    return 0

def _init_oktimefirstsol ():
    return 0

def _init_oktimelastsol ():
    return 0

def _init_solved ():
    return False

def _init_oksolved ():
    return False

def _init_plansoln ():
    return []

def _init_okplansoln ():
    return []

def _init_values ():
    return []

def _init_uppervalue ():
    return 0

def _init_lowervalue ():
    return 0

def _init_lengths ():
    return []

def _init_maxlength ():
    return 0

def _init_minlength ():
    return 0

def _init_sumruntime ():
    return 0

def _init_minruntime ():
    return 0

def _init_maxruntime ():
    return 0

def _init_summemend ():
    return 0

def _init_minmemend ():
    return 0

def _init_maxmemend ():
    return 0

def _init_summemmax ():
    return 0

def _init_minmemmax ():
    return 0

def _init_maxmemmax ():
    return 0

def _init_sumnumsols ():
    return 0

def _init_oksumnumsols ():
    return 0

def _init_numprobs ():
    return 0

def _init_numsolved ():
    return 0

def _init_oknumsolved ():
    return 0

def _init_numfails ():
    return 0

def _init_timefails ():
    return []

def _init_memfails ():
    return []

def _init_unexfails ():
    return []

def _init_numtimefails ():
    return 0

def _init_nummemfails ():
    return 0

def _init_numunexfails ():
    return 0

def _init_minvalue ():
    return 0

def _init_maxvalue ():
    return 0


# propagate

# for each elaborated var add a function _propagate_%var% () which just returns
# the new value of an elaborated variable from a 'prev' value when prefixing its
# key by another 'subkey'

def _propagate_sumruntime (subkey, prev):
    return prev

def _propagate_minruntime (subkey, prev):
    return prev

def _propagate_maxruntime (subkey, prev):
    return prev

def _propagate_summemend (subkey, prev):
    return prev

def _propagate_minmemend (subkey, prev):
    return prev

def _propagate_maxmemend (subkey, prev):
    return prev

def _propagate_summemmax (subkey, prev):
    return prev

def _propagate_minmemmax (subkey, prev):
    return prev

def _propagate_maxmemmax (subkey, prev):
    return prev

def _propagate_sumnumsols (subkey, prev):
    return prev

def _propagate_oksumnumsols (subkey, prev):
    return prev

def _propagate_numprobs (subkey, prev):
    return prev

def _propagate_numsolved (subkey, prev):
    return prev

def _propagate_oknumsolved (subkey, prev):
    return prev

def _propagate_numfails (subkey, prev):
    return prev

def _propagate_timefails (subkey, prev):
    return prev

def _propagate_memfails (subkey, prev):
    return prev

def _propagate_unexfails (subkey, prev):
    return prev

def _propagate_numtimefails (subkey, prev):
    return prev

def _propagate_nummemfails (subkey, prev):
    return prev

def _propagate_numunexfails (subkey, prev):
    return prev

def _propagate_minvalue (subkey, prev):
    return prev

def _propagate_maxvalue (subkey, prev):
    return prev


# add

# computes the new value of an elaborated variable which results of adding
# (joining, or merging) two values: vala and valb

def _add_sumruntime (vala, valb):
    return vala + valb

def _add_minruntime (vala, valb):
    return min (vala, valb)

def _add_maxruntime (vala, valb):
    return max (vala, valb)

def _add_summemend (vala, valb):
    return vala + valb

def _add_minmemend (vala, valb):
    return min (vala, valb)

def _add_maxmemend (vala, valb):
    return max (vala, valb)

def _add_summemmax (vala, valb):
    return vala + valb

def _add_minmemmax (vala, valb):
    return min ( vala, valb )

def _add_maxmemmax (vala, valb):
    return max ( vala, valb )

def _add_sumnumsols (vala, valb):
    return vala+valb

def _add_oksumnumsols (vala, valb):
    if (vala=='?' or valb=='?'):
        return '?'
    else:
        return vala + valb

def _add_numprobs (vala, valb):
    return vala + valb

def _add_numsolved (vala, valb):
    return vala + valb

def _add_oknumsolved (vala, valb):
    if (vala=='?' or valb=='?'):
        return '?'
    else:
        return vala + valb

def _add_numfails (vala, valb):
    return vala + valb

def _add_timefails (vala, valb):
    return vala + valb

def _add_memfails (vala, valb):
    return vala + valb

def _add_unexfails (vala, valb):
    return vala + valb

def _add_numtimefails (vala, valb):
    return vala + valb

def _add_nummemfails (vala, valb):
    return vala + valb

def _add_numunexfails (vala, valb):
    return vala + valb

def _add_minvalue (vala, valb):
    if (vala=='?' or valb=='?'):
        return '?'
    else:
        return min (vala, valb)

def _add_maxvalue (vala, valb):
    if (vala=='?' or valb=='?'):
        return '?'
    else:
        return max (vala, valb)


# Local Variables:
# mode:python
# fill-column:80
# End:
