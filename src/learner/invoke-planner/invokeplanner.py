#!/usr/bin/python
# -----------------------------------------------------------------------------
#
#     Copyright Malte Helmert, 2008
#               Carlos Linares Lopez, 2011
#               Sergio Nunez and Isabel Cenamor, 2014
# -----------------------------------------------------------------------------

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import datetime         # date/time
import fnmatch          # Unix filename matching
import getopt           # variable-length params
import getpass          # getuser
import logging          # loggers
import os               # path and process management
import re               # matching regex
import resource         # process resources
import shutil           # copy files and directories
import signal           # process management
import socket           # gethostname
import stat             # stat constants
import sys              # argv, exit
import time             # time mgmt

from string import Template     # to use placeholders in the logfile

import IPClog           # for handling IPC log files
import IPCstat          # sampling facilities
import argtools         # new argparse actions
import systools         # IPC process management
import timetools        # IPC timing management

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
CHECK_INTERVAL = 5           # how often we query the process group status
KILL_DELAY = 5               # how long we wait between SIGTERM and SIGKILL

# create the (rather simple) stats recorded during the execution phase
RUNTIME = IPCstat.IPCstat ("Overall running time (seconds)") 
RUNMEM  = IPCstat.IPCstat ("Overall memory (Mbytes)") 
SOLVED  = IPCstat.IPCstat ("Number of solved instances") 
NBSOLS  = IPCstat.IPCstat ("Number of overall solutions generated") 

LOGDICT = {'node': socket.gethostname (),       # extra data to be passed
           'user': getpass.getuser ()}          # to loggers

# -----------------------------------------------------------------------------

# funcs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# create_parser
#
# creates a command-line parser
#
# -----------------------------------------------------------------------------
def create_parser ():
    """
    creates a command-line parser
    """

    # create the parser
    parser = argparse.ArgumentParser (description="Run every input planner with every training problem")

    # now, add the arguments

    # Group of mandatory arguments
    mandatory = parser.add_argument_group ("Mandatory arguments", "The following arguments are required.")
    mandatory.add_argument ('-P', '--planner',
                            required=True,
                            metavar = 'REGEXP',
                            nargs = '+',
                            action = argtools.AppendAction,
                            help="planners are checked out and built")
    mandatory.add_argument ('-D', '--domain',
                            required=True,
                            help="Domain file")
    mandatory.add_argument ('-t', '--problems',
                            required=True,
                            help="Training problems folder")
    mandatory.add_argument ('-T', '--timeout',
                            required=True,
                            type=int,
                            help="the maximum allowed time for solving a particular instance in seconds")
    mandatory.add_argument ('-M', '--memory',
                            required=True,
                            type=int,
                            help="the maximum allowed (overall) memory for solving a particular instance in Gigabytes")

    # Group of logging services
    logging = parser.add_argument_group ('Logging', 'The following arguments specify various logging settings')
    logging.add_argument ('-l', '--logfile',
                          help = "name of the logfile where the output of the whole process is recorded. The following placeholders are automatically replaced by their values: $track, $subtrack, $planner and $domain. The current date and time is appended at the end. It is left at the target directory specified with --directory")

    # and return the parser
    return parser


# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params
# -----------------------------------------------------------------------------
def show_switches (planner, domain, problems, timeout, memory):
    planners_ID = []
    for i in planner:
        planner_name = i[i.rfind("/") + 1:]
        planners_ID.append(planner_name)

    """
    show a somehow beautified view of the current params
    """

    # logger settings
    logger = logging.getLogger('invokeplanner::show_switches')

    testsuffix = str ()
    logger.info ("""
-----------------------------------------------------------------------------
 * Planner   :  %s
 * Domain    :  %s
 * Problems  :  %s

 * Timeout   :  %i seconds
 * Memory    :  %i bytes
 -----------------------------------------------------------------------------\n""" % (planners_ID, domain, problems, timeout, memory), extra=LOGDICT)


# -----------------------------------------------------------------------------
# checkflags
#
# check the parameters provided by the user
# -----------------------------------------------------------------------------
def checkflags (timeout, memory):

    """
    check the parameters provided by the user
    """

    # logger settings
    logger = logging.getLogger('invokeplanner::checkflags')

    if (timeout <= 0):
        logger.critical (" The timeout param shall be positive!", extra=LOGDICT)
        raise ValueError

    if (memory <= 0):
        logger.critical (" The memory param shall be positive!", extra=LOGDICT)
        raise ValueError


# -----------------------------------------------------------------------------
# createlogger
#
# opens a file in write mode in the current directory in case a logfile is
# given. If not, it creates a basic logger. Messages above the given level are
# issued. 
#
# planner and domain are used as values for their respective placeholders
#
# it returns the name of the logfile recording all logrecords. If none has been
# created it returns the empty string
# -----------------------------------------------------------------------------
def createlogger (logfile, level, planner='', domain=''):

    """
    opens a file in write mode in the specified directory in case a logfile is
    given. If not, it creates a basic logger. Messages above the given level are
    issued

    domain are used as values for their respective placeholders

    it returns the name of the logfile recording all logrecords. If none has been
    created it returns the empty string
    """

    # create the log file either as a file stream or to the stdout
    if (logfile):

        # substitute the placeholders in logfile accordingly
        logfilename = os.path.abspath (os.path.join (".", get_logname (planner, domain, logfile)))
        logging.basicConfig (filename=logfilename, filemode = 'w', level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s") 

    else:
        logfilename = ''
        logging.basicConfig (level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")

    # and return the logfilename
    return logfilename


# -----------------------------------------------------------------------------
# get_logname
#
# compute the log filename from the given template
# -----------------------------------------------------------------------------
def get_logname (planner, domain, logfile):
    """
    compute the log filename from the given template
    """

    def flat (l):
        """
        returns a string with the items in l separated by a dash '-'
        """
        if (l):
            return reduce (lambda x,y: x + '-' + y, l)
        else:
            return ''

    # use the logbuild template to make the proper substitutions
    return Template (logfile).substitute (planner=flat (planner), domain=flat (domain))


# -----------------------------------------------------------------------------
# set_limit
#
# sets 'amount' as the maximum allowed capacity of the resource 'kind'
# -----------------------------------------------------------------------------
def set_limit(kind, amount):
    """
    sets 'amount' as the maximum allowed capacity of the resource 'kind'
    """

    try:
        resource.setrlimit(kind, (amount, amount))
    except OSError, e:
        logger = logging.getLogger('invokeplanner::set_limit')
        logger.critical (" %s in 'set_limit'\n" % e, extra=LOGDICT)


# -----------------------------------------------------------------------------
# kill_pgrp
#
# sends the signal sig to the process group pgrp
# -----------------------------------------------------------------------------
def kill_pgrp(pgrp, sig):
    """
    sends the signal sig to the process group pgrp
    """

    try:
        os.killpg(pgrp, sig)
    except OSError:
        pass


# -----------------------------------------------------------------------------
# get_solutiontimes
#
# return the solution time which is assumed to be equal to the time elapsed
# since the generation of the file problem.pddl until the generation of a new
# solution file
# -----------------------------------------------------------------------------
def get_solutiontimes ():

    """
    return the solution time which is assumed to be equal to the time elapsed
    since the generation of the file problem.pddl until the generation of a new
    solution file
    """

    # initialization
    soltimes = []

    # Look for any solution file 
    solfiles = sorted (filter (lambda x : (fnmatch.fnmatch (x, 'plan.soln*')), os.listdir ('.')))

    # in case it has found any
    if (len (solfiles) != 0):
        startime = os.stat ('./problem.pddl') [stat.ST_CTIME]
        soltimes = [os.stat (isolfile) [stat.ST_CTIME] - startime for isolfile in solfiles]

    # and return the solution times computed so far
    return soltimes


# -----------------------------------------------------------------------------
# fetch
#
# gather admin info to be shown up as log files for a particular run
# -----------------------------------------------------------------------------
def fetch (logprefix):

    """
    gather admin info to be shown up as log files for a particular run
    """

    # and now other log files for the sys info
    logver = IPClog.IPClog (logprefix + '-ver')
    logcpu = IPClog.IPClog (logprefix + '-cpu')
    logmem = IPClog.IPClog (logprefix + '-mem')

    sysdata = (open ('/proc/version', 'r').readlines (), 
               open ('/proc/cpuinfo', 'r').readlines (), 
               open ('/proc/meminfo', 'r').readlines ())

    logver.write ("\n\n * Version: %s\n\n" % sysdata [0])
    logcpu.write ("\n\n * CPUinfo:\n\n")
    for iline in sysdata [1]:
        logcpu.write (' ' + iline,)
    
    logmem.write ("\n\n * MEMinfo:\n\n")
    for iline in sysdata [2]:
        logmem.write (' ' + iline,)
    logmem.write ('\n')

    # close the log files
    logver.close ()
    logcpu.close ()
    logmem.close ()


# -----------------------------------------------------------------------------
# run
#
# executes the specified 'script' in the current directory to read the given
# 'domain' file, 'problem' file and to generate a particular 'output'. The
# output of the script is redirected to 'logfile'
#
# the 'iplanner' and 'idomain' are explicitly passed by to keep track of the
# overall running time for all planners and domains. These are just strings used
# to reference them in the corresponding IPCstat
#
# the default computational resources are 15 minutes and 4 Gigabytes. Time is
# measured in seconds and memory in bytes
#
# note that logfile is here an IPClog file and not a standard python logger
# -----------------------------------------------------------------------------
def run (script, iplanner, idomain, directory, domain, problem, output, logfile, 
         timeout=900, memory=4294967296, multicore=False, dck=False):

    """
    executes the specified 'script' in the current directory to read the
    given 'domain' file, 'problem' file and to generate a particular
    'output'. The output of the script is redirected to 'logfile'

    the 'iplanner' and 'idomain' are explicitly passed by to keep track of the
    overall running time for all planners and domains. These are just strings
    used to reference them in the corresponding IPCstat
    
    the default computational resources are 15 minutes and 4 Gigabytes. Time is
    measured in seconds and memory in bytes
    
    note that logfile is here an IPClog file and not a standard python logger
    """

    # logger settings
    logger = logging.getLogger ("invokeplanner::run")

    # show an info message
    logger.info (" Running '%s' in '%s' ..." % (script, directory), extra=LOGDICT)

    # create a standard log file
    logstream = IPClog.IPClog (logfile + '-log')

    # show the header
    logstream.write ("\n\n Current working directory: %s" % directory)
    logstream.write ("\n Timeout: %i seconds" % timeout)
    logstream.write ("\n Memory : %i bytes\n" % memory)

    # write info on the linux version, cpu and mem available
    sysdata = fetch (logfile)

    # Initialization
    total_vsize = 0
    set_alarm = False

    # change cwd
    cwd = os.getcwd ()
    os.chdir (directory)

    # create a timer
    runtimer = timetools.Timer ()

    # Now, a child is created which will host the planner execution while this
    # process simply monitors the resource comsumption. If any is exceeded the
    # whole process group is killed
    with runtimer:

        child_pid = os.fork()
        if not child_pid:                                            # child's code
            os.setpgrp()
            if (not multicore):
                set_limit(resource.RLIMIT_CPU, timeout)
            set_limit(resource.RLIMIT_AS, memory)
            set_limit(resource.RLIMIT_CORE, 0)
            for fd_no, filename in [(1, "./planner.log"), (2, "./planner.err")]:
                os.close(fd_no)
                fd = os.open(filename, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0666)
                assert fd == fd_no, fd
            if set_alarm:
                signal.alarm(timeout)

            # since the learning with control knowledge subtrack requires an
            # additional param, it is passed by here if that is the case
            if (dck):
                os.execl("./plan", "./plan", "domain.pddl", "problem.pddl", "plan.soln", "dck/" + idomain)
            else:
                os.execl("./plan", "./plan", "domain.pddl", "problem.pddl", "plan.soln")

        max_mem   = 0
        real_time = 0
        while True:
            time.sleep(CHECK_INTERVAL)
            real_time += CHECK_INTERVAL

            group = systools.ProcessGroup(child_pid)

            # Generate the children information before the waitpid call to avoid a
            # race condition. This way, we know that the child_pid is a descendant.
            if os.waitpid(child_pid, os.WNOHANG) != (0, 0):
                break

            # get the total time and memory usage
            process_time = real_time
            total_time = group.total_time()
            total_vsize = group.total_vsize()
            num_processes = group.total_processes ()
            num_threads = group.total_threads ()
            logstream.write ("\n [real-time %d] total_time: %.2f"  % (real_time, total_time))
            logstream.write ("\n [real-time %d] total_vsize: %.2f" % (real_time, total_vsize))
            logstream.write ("\n [real-time %d] num_processes: %d" % (real_time, num_processes))
            logstream.write ("\n [real-time %d] num_threads: %d"   % (real_time, num_threads))

            # update the maximum memory usage
            max_mem = max (max_mem, total_vsize)

            # if multicore ain't enabled, the usual rules apply
            if (not multicore):
                try_term = (total_time >= timeout or
                            real_time >= 1.5 * timeout)
                try_kill = (total_time >= timeout + KILL_DELAY or
                            real_time >= 1.5 * timeout + KILL_DELAY)

            # otherwise, use the parent time (i.e., the process starting the
            # whole planning process)
            else:
                try_term = (process_time >= timeout or
                            real_time >= 1.5 * timeout)
                try_kill = (process_time >= timeout + KILL_DELAY or
                            real_time >= 1.5 * timeout + KILL_DELAY)

            term_attempted = False
            if try_term and not term_attempted:
                logstream.write ("\n aborting children with SIGTERM...")
                logstream.write ("\n children found: %s\n" % group.pids())
                kill_pgrp(child_pid, signal.SIGTERM)
                term_attempted = True
            elif term_attempted and try_kill:
                logstream.write ("\n aborting children with SIGKILL...")
                logstream.write ("\n children found: %s\n" % group.pids())
                kill_pgrp(child_pid, signal.SIGKILL)

        # Even if we got here, there may be orphaned children or something we may
        # have missed due to a race condition. Check for that and kill.
        group = systools.ProcessGroup(child_pid)
        if group:
            # If we have reason to suspect someone still lives, first try to kill
            # them nicely and wait a bit.
            logstream.write ("\n aborting orphaned children with SIGTERM...")
            logstream.write ("\n children found: %s" % group.pids())
            kill_pgrp(child_pid, signal.SIGTERM)
            time.sleep(1)

        # Either way, kill properly for good measure. Note that it's not clear if
        # checking the ProcessGroup for emptiness is reliable, because reading the
        # process table may not be atomic, so for this last blow, we don't do an
        # emptiness test.
        kill_pgrp(child_pid, signal.SIGKILL)

        # check whether the planner actually found solutions or not
        solutiontimes = get_solutiontimes ()

        if (len (solutiontimes) == 0):
            logstream.write ("\n No solutions found!")
        else:
            logstream.write ("\n Number of solutions found: %i" % len (solutiontimes))
            logstream.write ("\n Time/solution            : %s" % solutiontimes)

        # return to the previous directory
        os.chdir (cwd)

    logstream.write ("\n Overall runtime: %i seconds" % runtimer.elapsed ())
    logstream.write ("\n Overall memory : %.2f Mbytes" % total_vsize)
    logstream.write ("\n Maximum memory : %.2f Mbytes\n\n" % max_mem)

    # and now, update the time it took to run problems for this planner/domain
    # and also the memory usage and the number of problems generated so far
    RUNTIME.accumulate (iplanner, idomain, runtimer.elapsed ())
    RUNMEM.accumulate  (iplanner, idomain, total_vsize)
    SOLVED.accumulate  (iplanner, idomain, int (len (solutiontimes)>0))
    NBSOLS.accumulate  (iplanner, idomain, len (solutiontimes))
    
    # close the log file
    logstream.close ()
    
    
# -----------------------------------------------------------------------------
# collect
#
# it goes to the given directory and extracts all files that are expected to
# have been created by running the script on a working directory. It writes the
# output in a directory which results from the given planner/domain
#
# logfile is the compilation log file
# -----------------------------------------------------------------------------
def collect (workingdir, planner, domain, problem):

    """
    it goes to the given directory and extracts all files that are expected to
    have been created by running the script on a working directory. It writes
    the output in a directory which results from the given planner/domain

    logfile is the compilation log file
    """

    def movedata (file, src, dst):
        """
        copy the file in src to dst. It issues an exception if the file does not
        exist or cannot be read
        """

        # logger settings
        logger = logging.getLogger ('invokeplanner::movedata')

        source = os.path.join (src, file)
        if (not os.access (source, os.F_OK) or
            not os.access (source, os.R_OK)):
            logger.critical (" The file '%s' either does not exist or cannot be read" % source,
                             extra=LOGDICT)
        shutil.move (source, dst)

    # logger settings
    logger = logging.getLogger('invokeplanner::collect')

    # compute the name of the results directory for this case
    resultsdir = workingdir + '/../results/' + planner + '/' + domain + '/' + problem

    # in case it exists, raise an error
    if (os.access (resultsdir, os.F_OK)):
        logger.critical (" The directory '%s' already exists!" % resultsdir,
                         extra=LOGDICT)
        raise IOError

    logger.info (" Collecting results in %s" % resultsdir, extra=LOGDICT)

    # create it
    os.makedirs (resultsdir)

    # and copy the relevant files from the workingdir to the resultsdir
    command = "cp " + workingdir + "/../build-" + planner + ".log " + resultsdir
    os.system(command)

    command = "cp " + workingdir + "/original-domain.pddl " + resultsdir + "/domain.pddl"
    os.system(command)

    command = "cp " + workingdir + "/original-problem.pddl " + resultsdir + "/problem.pddl"
    os.system(command)

    movedata ('planner.err' , workingdir, resultsdir)
    movedata ('planner.log' , workingdir, resultsdir)

    prefix = '_' + planner + '-' + domain + '.' + problem
    movedata (prefix + '-log', workingdir, resultsdir)
    movedata (prefix + '-cpu', workingdir, resultsdir)
    movedata (prefix + '-mem', workingdir, resultsdir)
    movedata (prefix + '-ver', workingdir, resultsdir)

    # get all the solution files
    files = os.listdir (workingdir)
    solfiles = filter (lambda x : (fnmatch.fnmatch (x, 'plan.soln*')), files)
    for isolfile in solfiles:
        movedata (isolfile, workingdir, resultsdir)
   


# -----------------------------------------------------------------------------
# setup
#
# takes the specified planner/domain from the src folder and sets up the
# environment to run the experiment.
# -----------------------------------------------------------------------------

def setup (planner, domain, problems, timeout=900, memory=4294967296):
    """
    takes the specified planner/domain from the src folder
    and sets up the environment to run the experiment.
    """

    # logger settings
    logger = logging.getLogger('invokeplanner::setup')
    logger.info (" Building planners ...", extra=LOGDICT)
    builtplanner = []

    # first, copy and compile each planner
    for current_planner in planner:
        planner_name = current_planner[current_planner.rfind("/") + 1:]
        build_name = "build-" + planner_name + ".log"

        if(os.path.isdir("./" + planner_name)):
            logger.info("The folder \"" + planner_name + "\" already exists, we remove it", extra=LOGDICT)
            command = "rm -rf ./" + planner_name
            os.system(command)

        logger.info("Copying " + planner_name, extra=LOGDICT)
        command = "cp -r " + current_planner + " ."
        os.system(command)

        if(os.path.isfile("./" + build_name)):
            logger.info("The file \"" + build_name + "\" already exists, we remove it", extra=LOGDICT)
            command = "rm -rf ./" + build_name
            os.system(command)

        logger.info("Compiling " + planner_name, extra=LOGDICT)
        command = "./" + planner_name + "/build > " + build_name + " 2>&1"
        os.system(command)
        builtplanner.append(planner_name)


    # now, build the testsets for this domain under the specified track/subtrack
    domain_name = domain[domain.rfind("/") + 1: domain.rfind(".")]
    logger.info (" Building domain " + domain_name, extra=LOGDICT)

    if(os.path.isdir("./" + domain_name)):
        logger.info("The folder \"" + domain_name + "\" already exists, we remove it", extra=LOGDICT)
        command = "rm -rf ./" + domain_name
        os.system(command)

    command = "mkdir ./" + domain_name
    os.system(command)
    command = "mkdir ./" + domain_name + "/domain"
    os.system(command)
    command = "cp " + domain + " " + domain_name + "/domain/domain.pddl"
    os.system(command)
    command = "mkdir ./" + domain_name + "/problems"
    os.system(command)
    command = "mkdir ./" + domain_name + "/problems_wac"
    os.system(command)
    counter = 0
    for test in sorted(os.listdir(problems)):
        suffix = "%03i" % counter
        command = "cp " + problems + "/" + test + " " + domain_name + "/problems/problem-" + suffix + ".pddl"
        os.system(command)
        counter += 1


    # Parsing problems
    print "\nParsing problems...\n"
    command = "python2.7 ../parser/clean_typing.py ./" + domain_name + "/problems/" 
    os.system(command)


    # Removing action costs for LPG and SGPLAN
    command = "python2.7 ../parser/clean_action_costs.py ./" + domain_name + "/domain/domain.pddl ./" + domain_name + "/domain/ ./" + \
              domain_name + "/problems/ ./" + domain_name + "/problems_wac"
    os.system(command)


    print "\nRunning each candidate planner with every training problem...\n"
    # now, for every built planner
    for iplanner in builtplanner:

        # and for ever problem from domain_name
        for test in sorted(os.listdir(domain_name + "/problems/")):

            if(test.find("_wtp") >= 0):
                # get the id of this testset
                suffix = test[test.find("-") + 1: test.rfind("_wtp.")]
                print "Suffix: " + str(suffix)
                if (len (suffix) < 2):
                    logger.critical (""" it was not possible to extract the suffix from testset '%s'""" % (test), extra=LOGDICT)
                    exit ()
            
                # compute the name of the working directory to be used in this
                # iteration
                workingdir = './_' + iplanner + '.' + domain_name + '.' + suffix

                # if the working directory exists, then abort
                if (os.access (workingdir, os.F_OK)):
                    logger.critical (""" directory '%s' already exists in setup""" % (workingdir), 
                                     extra=LOGDICT)
                    exit ()

                # create a working directory with the compiled planner
                logger.info (" Building workingdir %s ..." % workingdir, extra=LOGDICT)
                shutil.copytree ('./' + iplanner, workingdir)

                # move the corresponding domain and problem files to this
                # working directory
                if((iplanner.find("lpg") >= 0) or (iplanner.find("sgplan") >= 0)):
                    shutil.copyfile ('./' + domain_name + '/domain/domain_wac.txt', 
                                     workingdir + '/domain.pddl')
                    shutil.copyfile ('./' + domain_name + '/problems_wac/' + test[:test.rfind(".")] + "_and_wac.txt",
                                     workingdir + '/problem.pddl')

                else:
                    shutil.copyfile ('./' + domain_name + '/domain/domain.pddl', 
                                     workingdir + '/domain.pddl')
                    shutil.copyfile ('./' + domain_name + '/problems/' + test,
                                     workingdir + '/problem.pddl')

                # Copy the original problem/domain
                shutil.copyfile ('./' + domain_name + '/domain/domain.pddl', 
                                 workingdir + '/original-domain.pddl')
                shutil.copyfile ('./' + domain_name + '/problems/' + test[:test.find("_wtp")] + ".pddl",
                                 workingdir + '/original-problem.pddl')


                # and now invoke the planner in the working directory with this
                # domain and problem and requesting to generate an output file
                # named 'output' - if this is the multicore (mco) subtrack then
                # allow the run script to use clock wall time instead of the
                # accumulated time of its children
                logname = workingdir + '/_' + iplanner + '-' + domain_name + '.' + suffix
                run ('plan', iplanner, domain_name, workingdir, 'domain.pddl', 'problem.pddl', 'output', 
                     logname, timeout, memory, False, False)
                collect (workingdir, iplanner, domain_name, suffix)

                # now, delete the working dir
                shutil.rmtree (workingdir)

        command = "rm -rf ./build-" + iplanner + ".log"
        os.system(command)

    command = "rm -rf ./" + domain_name
    os.system(command)

    for iplanner in builtplanner:
        command = "rm -rf ./" + iplanner
        os.system(command)


# -----------------------------------------------------------------------------
# show_stats
#
# shows the overall running times/memory for each planner/domain and the overall
# totals
# -----------------------------------------------------------------------------
def show_stats ():

    """
    shows the overall running times for each planner/domain and the overall totals
    """

    # logger settings
    logger = logging.getLogger('invokeplanner::show_stats')

    logger.info ('\n' + str (RUNTIME) + '\n', extra=LOGDICT)
    logger.info ('\n' + str (RUNMEM) + '\n', extra=LOGDICT)
    logger.info ('\n' + str (SOLVED) + '\n', extra=LOGDICT)
    logger.info ('\n' + str (NBSOLS) + '\n', extra=LOGDICT)


# -----------------------------------------------------------------------------
# dispatcher
#
# this class creates a dispatcher for automating the experiments. Besides, it
# creates specific __enter__ and __exit__ methods that are used to automate the
# e-mail notification
# -----------------------------------------------------------------------------
class dispatcher (object):
    """
    this class creates a dispatcher for automating the experiments. Besides, it
    creates specific __enter__ and __exit__ methods that are used to automate
    the e-mail notification
    """

    # Default constructor
    def __init__ (self, planner, domain, problems, logfile, timeout, memory):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._planner, self._domain, self._problems, self._logfile, self._timeout, self._memory) = \
         (planner, domain, problems, logfile, timeout, memory)


    # Execute the following body when building plannerss
    def __enter__ (self):
        """
        Execute the following body when building planners
        """

        # now, create the overall log file if anyone has been requested
        if (self._logfile):
            self._logfilename = self._logfile + '.' + datetime.datetime.now ().strftime ("%y-%m-%d.%H:%M:%S")
        else:
            self._logfilename = None
        self._logfilename = createlogger (self._logfilename, "INFO", self._planner, self._domain)

        # before proceeding, check that all parameters are correct
        checkflags (self._timeout, self._memory)


    # The following method sets up the environment for automating the experiments
    def invokeplanner (self):
        """
        The following method sets up the environment for automating the experiments
        """

        # logger settings
        logger = logging.getLogger("dispatcher::invokeplanner")

        # show the current params
        show_switches (self._planner, self._domain, self._problems, self._timeout, self._memory)

        # finally, run the experiments
        try:
            setup (self._planner, self._domain, self._problems, timeout=self._timeout, memory=self._memory)

            # and show the overall running time consumed per planner/domain and the
            # overall totals
            show_stats ()

        except Exception, msg:
            logger.critical (" An exception was caught. Exiting ... ", extra=LOGDICT)
            logger.critical (" %s" % msg, extra=LOGDICT)


    # Make sure that the automated e-mail notification is invoked everytime the
    # dispatcher is about to exit ---to whatever reason happens
    def __exit__ (self, type, value, traceback):

        # logger settings
        logger = logging.getLogger('dispatcher::__exit__')



# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    PROGRAM_NAME = sys.argv[0]              # get the program name

    # parse the arguments
    PARSER = create_parser ()
    ARGS = PARSER.parse_args ()

    # convert the memory (currently in Gigabytes) to bytes
    ARGS.memory *= 1024**3

    # Print args
    print "\nPlanner: " + str(ARGS.planner)
    print "Domain: " + str(ARGS.domain)
    print "Problems: " + str(ARGS.problems)
    print "Log file: " + str(ARGS.logfile)
    print "Timeout: " + str(ARGS.timeout)
    print "Memory: " + str(ARGS.memory) + "\n"

    # Now, enclose all the process in a with statement so that the automated
    # e-mail facility is called whatever happens inside this body
    DISPATCHER = dispatcher (ARGS.planner, ARGS.domain, ARGS.problems,
                             ARGS.logfile, ARGS.timeout, ARGS.memory)

    with DISPATCHER:
        
        # and request automating all the experiments
        DISPATCHER.invokeplanner ()



# Local Variables:
# mode:python
# fill-column:80
# End:
