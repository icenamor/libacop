#!/usr/bin/env python
#
# validate.py
# Description: Recursive validation of all depth 0 directories beneath a given one
# -----------------------------------------------------------------------------
#
# Started on  <Sun May 15 19:42:43 2011 Carlos Linares Lopez>
# Last update <Tuesday, 20 December 2011 23:35:13 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: validate.py 308 2011-12-20 23:08:29Z clinares                        $
# $Date:: 2011-12-21 00:08:29 +0100 (Wed, 21 Dec 2011)                       $
# $Revision:: 308                                                            $
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
Recursive validation of all depth 0 directories beneath a given one
"""

__version__  = '1.2'
__revision__ = '$Revision: 308 $'
__date__     = '$Date: 2011-12-21 00:08:29 +0100 (Wed, 21 Dec 2011) $'


# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import datetime         # date/time
import getopt           # variable-length params
import getpass          # getuser
import logging          # loggers
import os               # path and process management
import re               # regular expressions
import socket           # gethostname
import sys              # argv, exit
import time             # time mgmt

import PrettyTable      # beautified ascii output

import IPCini           # for accessing the ini configuration files

import argtools         # new argparse actions
import validatel0       # validation of level 0 directories

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
PROGRAM_VERSION = "1.2"

LOGDICT = {'node': socket.gethostname (),       # extra data to be passed
           'user': getpass.getuser ()}          # to loggers

# -----------------------------------------------------------------------------

# Funcs
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
    parser = argparse.ArgumentParser (description="Validates all the plan solution files that are found beneath a given directory")

    # now, add the arguments

    # Group of mandatory arguments
    mandatory = parser.add_argument_group ("Mandatory arguments", "The following arguments are required. Note that it is assumed that the INI configuration file is '~/.ipc.ini'")
    mandatory.add_argument ('-d', '--directory',
                            required=True,
                            help ="specifies the directory to examine. All terminal directories found beneath the given one will be validated" )

    # Group of configuration arguments
    conf = parser.add_argument_group ('Configuration arguments', 'The following arguments set various configuration parameters')
    conf.add_argument ('-i', '--ini',
                       metavar='INIFILE',
                       default = os.path.expanduser ('~/.ipc.ini'),
                       help = "If an INI configuration file is provided, then its contents are parsed when needed ---e.g., when issuing e-mails. If none is provided ~/.ipc.ini is tried by default")

    # Group of logging services
    logging = parser.add_argument_group ('Logging', 'The following arguments specify various logging settings')
    logging.add_argument ('-l', '--logfile',
                          help = "name of the logfile where the output of the whole process is recorded. The current date and time are appended at the end. It is left at the current directory unless a different path is specified")
    logging.add_argument ('-L', '--level',
                          choices=['INFO', 'WARNING', 'CRITICAL'],
                          default='INFO',
                          help="level of log messages. Messages of the same level or above are shown. By default, INFO, i.e., all messages are shown")
    logging.add_argument ('-e', '--email',
                          nargs = '+',
                          action= argtools.AppendAction,
                          help="sends an e-mail to the specified address upon completion. It uses the values of mailuser, mailpwd, smtp and port found in the [general] section of the INI configuration file specified with --ini")

    # Group of miscellaneous arguments
    misc = parser.add_argument_group ('Miscellaneous')
    misc.add_argument ('-v', '--verbose',
                       action='store_true',
                       help="shows additional information")
    misc.add_argument ('-V', '--version',
                       action='version',
                       version=" %s %s %s %s" % (sys.argv [0], PROGRAM_VERSION, __revision__[1:-1], __date__[1:-1]),
                       help="output version information and exit")

    # and return the parser
    return parser


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
    logger = logging.getLogger('validate::show_switches')

    logger.info (""" -----------------------------------------------------------------------------
 * directory : %s
 -----------------------------------------------------------------------------\n""" % (directory),
                 extra=LOGDICT)


# -----------------------------------------------------------------------------
# version
#
# shows version info
# -----------------------------------------------------------------------------
def version (log=False):

    """
    shows version info
    """

    if (log):

        logger = logging.getLogger ("builddomain::version")
        logger.info ("\n %s\n %s\n %s %s\n" % (__revision__[1:-2], __date__[1:-2], PROGRAM_NAME, PROGRAM_VERSION), extra=LOGDICT)

    else:
        print ("\n %s\n %s\n" % (__revision__[1:-1], __date__[1:-1]))
        print (" %s %s\n" % (PROGRAM_NAME, PROGRAM_VERSION))


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
    logger = logging.getLogger('validate::checkflags')

    # check that the specified directory exists indeed
    if (not os.path.exists (directory)):
        logger.critical (""" The directory given with --directory (%s) does not exist!
 Type '%s --help' for more information
""" % (directory, PROGRAM_NAME), extra=LOGDICT)
        raise ValueError


# -----------------------------------------------------------------------------
# validate
#
# validates all the level 0 directories that are beneath the specified
# one
#
# if 'error' is given, an error message is issued when a directory
# with no subdirectories misses some important files
#
# it returns the number of depth 0 directories validated, the number
# of them with correct solutions, the number of solution files
# validated and the number of them that were found successful
# -----------------------------------------------------------------------------
def validate (directory, verbose=False, error=False):

    """
    validates all the level 0 directories that are beneath the
    specified one
    
    if 'error' is given, an error message is issued when a directory
    with no subdirectories misses some important files
    
    it returns the number of depth 0 directories validated, the number
    of them with correct solutions, the number of solution files
    validated and the number of them that were found successful
    """

    # base condition - this is a level 0 directory
    try:
        validatel0.checkdepth0 (directory, error)

        # at this point, this directory is known to be of depth 0, so
        # validate it and return the number of solution files
        # validated and the number of them that were found to be
        # successful signaling also that only one directory has been
        # considered and whether it contained valid solutions or not
        (nbfiles, nbsuccessful) = validatel0.validate0 (directory, verbose, error)
        return ( 1, int (nbsuccessful > 0), nbfiles, nbsuccessful )

    # if an exception was raised, then this is not a depth 0
    # directory, just do nothing
    except Exception, message:
        pass

    # general case - this is not a depth 0 directory

    # traverse all directories beneath this one whose name does not
    # start with either '.' or '_'
    nbdirs = nbsols = nbfiles = nbsuccessful = 0
    subdirs = []
    for root, dirnames, filenames in os.walk (directory):
        if (root == directory):
            subdirs = filter (lambda x : x[0]!='.' and x[0]!='_', sorted (dirnames))
    
    for isubdir in subdirs:
        (inbdirs, inbsols, inbfiles, inbsuccessful) = \
            validate (directory + '/' + isubdir, verbose, error)

        # and update the number of depth 0 directories, the number of
        # them that have been solved, the number of solution files and
        # number of solution files that were found to be successful
        nbdirs += inbdirs
        nbsols += inbsols
        nbfiles += inbfiles
        nbsuccessful += inbsuccessful

    return (nbdirs, nbsols, nbfiles, nbsuccessful)


# -----------------------------------------------------------------------------
# show_output
#
# shows a table with a unique row that contains the number of depth 0
# directories validated, the number of them that had at least one
# solution, the number of solution files validated and how many were
# found to be successful
# -----------------------------------------------------------------------------
def show_output (nbdirs, nbsolved, nbfiles, nbsuccessful):

    """
    shows a table with a unique row that contains the number of depth
    0 directories validated, the number of them that had at least one
    solution, the number of solution files validated and how many were
    found to be successful
    """

    # logger settings
    logger = logging.getLogger('validate::show_output')

    # create a pretty table
    table = PrettyTable.PrettyTable (["# directories", "# solved", "# solution files", "# successful plans"])
    
    # write the only row or data
    table.add_row ([nbdirs, nbsolved, nbfiles, nbsuccessful])

    # and show it
    logger.info (table, extra=LOGDICT)


# -----------------------------------------------------------------------------
# dispatcher
#
# this class creates a dispatcher for validating results. Besides, it creates
# specific __enter__ and __exit__ methods that are used to automate the e-mail
# notification
# -----------------------------------------------------------------------------
class dispatcher (object):
    """
    this class creates a dispatcher for validating results. Besides, it creates
    specific __enter__ and __exit__ methods that are used to automate the e-mail
    notification
    """

    # Default constructor
    def __init__ (self, directory, inifilename, logfile, level, email, 
                  verbose=False, wxProgressDialog=None):
        """
        Default constructor
        """
        
        # copy the private attributes
        (self._directory, self._inifilename, self._logfile, self._level,
         self._email, self._verbose, self._wxProgressDialog) = \
         (directory, inifilename, logfile, level, 
          email, verbose, wxProgressDialog)
        

    # Execute the following body when validating results
    def __enter__ (self):
        """
        Execute the following body when validating results
        """

        if (self._logfile):
            self._logfilename = self._logfile + '.' + datetime.datetime.now ().strftime ("%y-%m-%d.%H:%M:%S")
        else:
            self._logfilename = None
        self._logfilename = createlogger (self._logfilename, self._level)

        # before proceeding, check that all parameters are correct
        checkflags (self._directory)


    # The following method sets up the environment for validating results
    def validate (self):
        """
        The following method sets up the environment for validating results
        """

        # logger settings
        logger = logging.getLogger("dispatcher:validate")

        # show the current version
        version (log=True)

        # in case a number of emails have been provided, check that a
        # mailuser/mailpwd/smtp/port is defined in the INI configuration file
        if (self._email):

            try:
                inifile = IPCini.IPCini (self._inifilename)
                self._mailuser = inifile.get_mailuser ()
                self._mailpwd  = inifile.get_mailpwd ()
                self._smtp     = inifile.get_smtp_server ()
                self._port     = int (inifile.get_smtp_port ())
            except:
                logger.critical (""" No mailuser/mailpwd/smtp/port information available in the ini configuration file.
 Run 'seed.py' providing both parameters or create a new session """, extra=LOGDICT)
                raise ValueError

        # check that the Automatic Validation Tool is available in the system
        validatel0.checkval ()

        # and validate the results
        (nbdirs, nbsolved, nbfiles, nbsuccessful) = validate (self._directory, verbose=self._verbose)

        # show the output
        show_output (nbdirs, nbsolved, nbfiles, nbsuccessful)

        # show an ack msg
        logger.info (" All the results in directory '%s' have been validated" % self._directory,
                     extra=LOGDICT)


    # Make sure that the automated e-mail notification is invoked everytime the
    # dispatcher is about to exit ---to whatever reason happens
    def __exit__ (self, type, value, traceback):
        """
        Make sure that the automated e-mail notification is invoked everytime
        the dispatcher is about to exit ---to whatever reason happens
        """

        # logger settings
        logger = logging.getLogger('dispatcher::__exit__')

        if (self._email):

            # issue an info message
            map (lambda recipee: logger.info (" Sending an automated e-mail to %s from Outter Space" % recipee,
                                              extra=LOGDICT), self._email)

            # set up the connection and identify yourself 
            mailer = mailtools.MailSender (self._smtp, self._port)
            mailer.open (self._mailuser, self._mailpwd)

            # prepare the body
            mailer += 'This is an automatic message from the Outter Space'
            mailer += 'Do not reply to this message!'
            mailer += 'Current local time: ' + time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())
            mailer += '-------------------------------------------------------------------------------\n'

            # in case a logfile was specified, add it to the body of the message
            if (self._logfilename):
                mailer.attach (self._logfilename)
            else:
                mailer += 'No logfile has been created - empty body!\n'

            mailer += '-------------------------------------------------------------------------------'
            mailer += 'The transcription ends here!'

            # and now send all messages to the list of recipients
            [mailer.send ('Outter Space', toaddr, 
                          subject='Automated validation (%s)' % self._directory)
             for toaddr in self._email]



# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    PROGRAM_NAME = sys.argv[0]              # get the program name

    # parse the arguments
    PARSER = create_parser ()
    ARGS = PARSER.parse_args ()

    # Now, enclose all the process in a with statement so that the automated
    # e-mail facility is called whatever happens inside this body
    DISPATCHER = dispatcher (ARGS.directory, ARGS.ini, ARGS.logfile, ARGS.level,
                             ARGS.email, ARGS.verbose)
    with DISPATCHER:
        
        # and request validating the results with the specified data
        DISPATCHER.validate ()


# Local Variables:
# mode:python
# fill-column:80
# End:
