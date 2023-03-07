#!/usr/bin/python
#
# systools.py
# Description: process management ---literally taken from the IPC 2008
# -----------------------------------------------------------------------------
#
# Started on  <Tue Mar  8 09:26:14 2011 Carlos Linares Lopez>
# Last update <Friday, 11 November 2011 23:03:05 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: systools.py 306 2011-11-11 22:25:37Z clinares                        $
# $Date:: 2011-11-11 23:25:37 +0100 (Fri, 11 Nov 2011)                       $
# $Revision:: 306                                                            $
# -----------------------------------------------------------------------------
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
#     Copyright Malte Helmert, 2008
#               Carlos Linares Lopez, 2011
# -----------------------------------------------------------------------------

"""
process management ---literally taken from the IPC 2008
"""

__version__  = '1.2'
__revision__ = '$Revision: 306 $'

import os

JIFFIES_PER_SECOND = 100

def partition(text, pattern):
    pos = text.find(pattern)
    if pos == -1:
        return text, "", ""
    else:
        return text[:pos], pattern, text[pos + len(pattern):]


def rpartition(text, pattern):
    pos = text.rfind(pattern)
    if pos == -1:
        return "", "", text
    else:
        return text[:pos], pattern, text[pos + len(pattern):]


class Process(object):
    def __init__(self, pid):
        stat = open("/proc/%d/stat" % pid).read()
        cmdline = open("/proc/%d/cmdline" % pid).read()

        # Don't use stat.split(): the command can contain spaces.
        # Be careful which "()" to match: the command name can contain
        # parentheses.
        prefix, lparen, rest = partition(stat, "(")
        command, rparen, suffix = rpartition(rest, ")")
        parts = suffix.split()

        self.pid = pid
        self.ppid = int(parts[1])
        self.pgrp = int(parts[2])
        self.utime = int(parts[11])
        self.stime = int(parts[12])
        self.cutime = int(parts[13])
        self.cstime = int(parts[14])
        self.numthreads = int (parts[17])
        self.vsize = int(parts[20])
        self.cmdline = cmdline.rstrip("\0\n").replace("\0", " ")

    def total_time(self):
        return self.utime + self.stime + self.cutime + self.cstime


def read_processes():
    for filename in os.listdir("/proc"):
        if filename.isdigit():
            pid = int(filename)
            # Be careful about a race conditions here: The process
            # may have disappeared after the os.listdir call.
            try:
                yield Process(pid)
            except EnvironmentError:
                pass


class ProcessGroup(object):
    def __init__(self, pgrp):
        self.processes = [process for process in read_processes()
                          if process.pgrp == pgrp]

    def __nonzero__(self):
        return bool(self.processes)

    def pids(self):
        return [p.pid for p in self.processes]

    def total_time(self):
        """
        Cumulated time for this process group, in seconds
        """
        
        total_jiffies = sum([p.total_time() for p in self.processes])
        return total_jiffies / float(JIFFIES_PER_SECOND)
                
    def total_vsize(self):
        """
        Cumulated virtual memory for this process group, in MB
        """
        
        total_bytes = sum([p.vsize for p in self.processes])
        return total_bytes / float(2 ** 20)

    def total_processes (self):
        """
        return the total number of processes in this group
        """

        return (len (self.processes))

    def total_threads (self):
        """
        return the total number of threads of all processes in this group
        """

        return sum ([p.numthreads for p in self.processes])


# Local Variables:
# mode:python
# fill-column:80
# End:
