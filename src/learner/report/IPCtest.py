#!/usr/bin/python
#
# IPCtest.py
# Description: provides means to perform statistical tests of various types
# -----------------------------------------------------------------------------
#
# Started on  <Thu May 10 14:44:13 2012 Carlos Linares Lopez>
# Last update <Sunday, 15 July 2012 16:15:45 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: IPCtest.py 322 2012-07-16 07:59:19Z clinares                         $
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
provides means to perform statistical tests of various types
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.3'
__revision__ = '$Revision: 322 $'

# the following string identifies entries to be removed
NOENTRY = -1

# formats recognized for printing 
NB_FORMATS = 5
TABLE, OCTAVE, HTML, EXCEL, WIKI = range (0, NB_FORMATS)

# the following variable stores the number of tests that can be performed with
# this script
NBTESTS = 4

# the name of the tests is specified below
MANNWHITNEYU, TTEST, WILCOXON, BINOMIAL = range (0,NBTESTS)

# the names of the tests as they are shown in the final report are described
# next
TESTS = {
    MANNWHITNEYU : "Mann-Whitney U",
    TTEST        : "T-Test",
    WILCOXON     : "Wilcoxon signed-rank test",
    BINOMIAL     : "Binomial test"}

# the acronyms used to refer to each particular test are:
ACRONYMS = {
    MANNWHITNEYU : 'mw',
    TTEST        : 'tt',
    WILCOXON     : 'wx',
    BINOMIAL     : 'bt'
}

# finally, the description of the test is the following
DESCS = {
    MANNWHITNEYU : "Computes the Mann-Whitney rank test on two samples. It assesses whether one of two samples of\n independent observations tends to have larger values than the other. This test corrects for ties and\n by default uses a continuity correction. The reported p-value is for a one-sided hypothesis, to get\n the two-sided p-value multiply the returned p-value by 2.",
    TTEST        : "Calculates the T-test for the means of two independent samples of scores.\n This is a two-sided test for the null hypothesis that two independent samples have identical average\n (expected) values.\n We can use this test, if we observe two independent samples from the same or different population,\n e.g. exam scores of boys and girls or of two ethnic groups. The test measures whether the average\n (expected) value differs significantly across samples. If we observe a large p-value, for example\n larger than 0.05 or 0.1, then we cannot reject the null hypothesis of identical average scores. If\n the p-value is smaller than the threshold, e.g. 1%, 5% or 10%, then we reject the null hypothesis\n of equal averages.",
    WILCOXON     : "Calculate the Wilcoxon signed-rank test.\n The Wilcoxon signed-rank test tests the null hypothesis that two related samples come from the same\n distribution. It is a a non-parametric version of the paired T-test and it is therefore a two-sided\n test. Both distributions shall have the same number of items",
    BINOMIAL     : "Perform a binomial two-sided sign test. It computes the number n of times that the serie shown in\n the row behaves differently than the serie shown in the column. It returns the probability according\n to a binomial distribution with p=0.5 that the number of times that the serie shown in the row takes\n values larger than the serie shown in the column equals at least the number of times that this\n difference was observed.\n If this probability is less or equal than a given threshold, e.g., 0.01, 0.05 or 0.1, then reject\n the null hypothesis and assume that the serie shown in the column is significantly smaller"}


# imports
# -----------------------------------------------------------------------------
import datetime                 # for printing current date and time

import numpy                    # arbitrary numerical precision
import scipy                    # scientific analysis in python
import scipy.stats              # statistical analysis

import pyExcelerator.Workbook   # excel workbooks
import pyExcelerator.Style      # excel styles
import PrettyTable              # for creating pretty tables

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IPCtest
#
#     This class stores two series of data and provides various means
#     to perform statistical tests with them
# -----------------------------------------------------------------------------
class IPCtest:
    """
    This class stores two series of data and provides various means to
    perform statistical tests with them
    """

    # default constructor
    def __init__ (self, matcher, noentry, seriea = [], serieb = []):
        """
        Default constructor
        """
        
        # compute the pairwise relations of both series up to the shortest one
        pairs = zip (seriea, serieb)
        # print " matcher: %s" % matcher
        # print " seriea : %s" % seriea
        # print " serieb : %s" % serieb
        # print " pairs  : %s" % pairs
        
        # filter those entries according to 'matcher' and store them in two
        # dedicated series
        self._seriea = []
        self._serieb = []
        for ipair in pairs:
            if (matcher == 'or' and 
                ((ipair[0]!=NOENTRY or ipair[1]!=NOENTRY))):
                self._seriea.append (ipair [0])
                self._serieb.append (ipair [1])

            elif (matcher == 'and' and
                  (ipair[0]!=NOENTRY and ipair[1]!=NOENTRY)):
                self._seriea.append (ipair [0])
                self._serieb.append (ipair [1])

            elif (matcher == 'all'):
                self._seriea.append (ipair [0])
                self._serieb.append (ipair [1])

            elif (matcher not in ['or', 'and', 'all']):
                print """
 Fatal Error - Unknown matcher '%s'
""" % matcher
                raise KeyError

        # and now, add to the longest serie the items that cannot be compared
        # with the smallest. In the following computations it is assumed that an
        # unexiting entry equals NOENTRY to all effects
        
        # if the selected matcher is all then all the remaining items are added
        # to the longest list
        if (matcher == 'all'):
            self._seriea += seriea [len (pairs):]
            self._serieb += serieb [len (pairs):]

        # otherwise, only if the matcher equals or all the remaining *valid*
        # entries are accepted
        elif (matcher == 'or'):
            self._seriea += filter (lambda (x):x!=NOENTRY, seriea [len (pairs):])
            self._serieb += filter (lambda (x):x!=NOENTRY, serieb [len (pairs):])

        # finally, substitute all the non-filtered entries with the noentry
        # value
        self._seriea = [ientry if (ientry != NOENTRY) else noentry for ientry in self._seriea]
        self._serieb = [ientry if (ientry != NOENTRY) else noentry for ientry in self._serieb]

        # print " self._seriea : %s" % self._seriea
        # print " self._serieb : %s" % self._serieb
        # print

    # methods

    # performs the requested statistical test with the series A and B stored in
    # this instance
    def test (self, test):
        """
        performs the requested statistical test with the series A and B stored
        in this instance
        """

        # check the test is among the known ones
        if (test not in range (0, NBTESTS)):

            print """
 Fatal Error - Unknown test '%i' in IPCtest.test""" % test
            raise IndexError

        # invoke the handler that corresponds to the given index
        do_handler = "do_%s (self._seriea, self._serieb)" % ACRONYMS [test]
            
        # and just return the result of the invocation
        try:
            return eval (do_handler)

        except Exception, message:
            return (-1, message)


# -----------------------------------------------------------------------------
# IPCtests
#
#     This class automates the realization of an arbitrary number of tests over
#     arbitrary collections of data
# -----------------------------------------------------------------------------
class IPCtests:
    """
    This class automates the realization of an arbitrary number of tests over
    arbitrary collections of data
    """

    # default constructor
    def __init__ (self, series, tests, matcher, noentry):
        """
        this constructor just receives a dictionary of series to analyze and the
        tests to perform with them. 

        The key of the dictionary is the name of the serie and its value is the
        list to analyze. This class performs pairwise analysis of all the series
        enclosed in the series

        The tests are just the list of statistical tests to perform on the lists
        of data

        The matcher shall be either 'and', 'or' or 'all' and it specifies how to
        accept pairwise associations of two series

        noentry indicates default values for the unfiltered entries
        """

        # just store the arguments as private attributes of this instance
        (self._series, self._tests, 
         self._matcher, self._noentry) = \
         (series, tests, 
          matcher, noentry)

        # the following dictionary stores the p values reported by the different
        # statistical tests. It consists of a dictionary whose first key is the
        # type of statistical test. The next two keys hold the name of two
        # different series. Finally, the value is the p-value that results of
        # the statistical test of those two series. It is initialized empty
        self._p = {}

        # by default, set the table format
        self._format = TABLE

        # make this an unnamed report
        self._name = 'unnamed'

    # operator overloading

    # printing service
    def __str__ (self):
        """
        printing service
        """
        
        # check there are some results to print
        if (not self._p):
            return " Warning - No tests have been performed yet! (empty p-values)"

        # and now invoke the corresponding service
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

    # set the printing format
    def set_format (self, format):
        """
        set the printing format
        """
        
        if (format not in range (0, NB_FORMATS)):
            print """
 Error - Unrecognized format style %s""" % format
            raise IndexError

        self._format = format


    # sets a name for these reports
    def set_name (self, name):
        """
        sets a name 
        """

        self._name = name


    # the following method goes through all the statistical tests and series and
    # performs them
    def tests (self):
        """
        the following method goes through all the statistical tests and series
        and performs them
        """

        # Perform all the statistical tests
        for itest in self._tests:

            # check these series are suitable for the selected analysis. Only if
            # they look properly arranged, the test is performed. This
            # particular action is performed using handlers
            check_handler = "check_%s (self._series)" % ACRONYMS [itest]
            if (eval (check_handler)):

                # if this test is not already in _p store it
                if (itest not in self._p):
                    self._p [itest] = {}

                # for every particular serie in the private dictionary of series
                for iserie in self._series:

                    # if iserie not in _p add this key
                    if (iserie not in self._p [itest]):
                        self._p [itest][iserie] = {}

                    for jserie in self._series:

                        # just only in case they are different
                        if (iserie != jserie):

                            # create an IPCtest with these two series
                            test = IPCtest (self._matcher, self._noentry, 
                                            self._series [iserie], self._series [jserie])

                            # perform the statistical test and store the resulting
                            # p-value according to the selection made in this instance
                            self._p [itest][iserie][jserie] = test.test (itest) [1]

            # otherwise, ...
            else:

                print """ Skipping test ... 
"""

    # printing services

    # print the contents of this class as a pretty table
    def print_table (self):
        """
        print the contents of this class as a pretty table
        """

        # initialization
        sout = ''

        # distinguish the different keywords according to the format
        newline={False:"<br>", True: '\n'}[self._format==TABLE]
        boldopen={False:"<b>", True: ''}[self._format==TABLE]
        boldclose={False:"</b>", True: ''}[self._format==TABLE]
        emphasizeopen={False:"<em>", True: ''}[self._format==TABLE]
        emphasizeclose={False:"</em>", True: ''}[self._format==TABLE]

        # for all tests
        for itest in self._tests:

            # check whether this test was performed or not
            if (itest not in self._p):
                continue

            # now, create a pretty table and add the headers
            table = PrettyTable.PrettyTable ([''] + self._series.keys ())

            # now, add the data rows, for each serie
            for iserie in self._series:

                # start this row with the name of this serie
                thisrow = [iserie]

                # and now, for all the other series
                for jserie in self._series:

                    # if both series are not the same
                    if (iserie != jserie):

                        # add the p-value of this particular combination
                        thisrow.append (self._p [itest][iserie][jserie])

                    # otherwise, add a dash
                    else:

                        thisrow.append ('---')

                # and add this row
                table.add_row (thisrow)

            # now, according to the style, get the corresponding string (either an
            # ascii pretty table or html code)
            if (self._format ==  TABLE):
                table.set_style (PrettyTable.DEFAULT)
                sout += (" name: %s\n" % self._name) + table.get_string ()
            elif (self._format == HTML):
                sout += "<h1>name: %s</h1>\n%s" % (self._name, table.get_html_string ())

            # and now, add the footer
            sout += newline
            sout += " %s%s%s : %s\n" % (boldopen, TESTS [itest], boldclose, DESCS [itest].replace ("\n", newline))

            sout += newline
            sout += " %screated by IPCtest %s (%s), %s%s" % (emphasizeopen,
                                                             __version__, __revision__ [1:-2],
                                                             datetime.datetime.now ().strftime ("%c"),
                                                             emphasizeclose)
            sout += newline

        return sout
        

    # print the contents of this class in octave format
    def print_octave (self):
        """
        print the contents of this class in octave format
        """

        # initialization
        sout = ''

        # for all the statistical tests requested
        for itest in self._tests:

            # check whether this test was performed or not
            if (itest not in self._p):
                continue

            # compute the header
            sout += "# created by IPCtest %s (%s), %s\n" % (__version__, __revision__ [1:-2],
                                                            datetime.datetime.now ().strftime ("%c"))
            sout += "# name: %s\n" % self._name
            sout += "# type: matrix\n"
            sout += "# rows: %i\n" % len (self._series)
            sout += "# columns: %i\n" % len (self._series)

            # create the lines with the requested data
            for iserie in self._series:
                for jserie in self._series:
                    if (iserie != jserie):
                        sout += "%s " % self._p [itest][iserie][jserie]
                    else:
                        sout += "0.0 "
                sout += '\n'

            # compute the footer
            sout += "# %s: %s\n" % (TESTS [itest], DESCS [itest].replace ("\n","\n#"))
            sout += "# Warning - entries on the main diagonal are marked with 0.0 to remind\n"
            sout += "#           the user that they are not relevant"

        # return the whole string
        return sout


    # show all data in Excel worksheets within the same document
    def print_excel (self):
        """
        show all data in Excel worksheets within the same document
        """

        # create an Excel workbook
        wb = pyExcelerator.Workbook ()

        # create the styles
        style = pyExcelerator.Style.XFStyle ()

        # for keys
        hstyle = pyExcelerator.XFStyle ()
        hstyle.font.name = "Arial"
        hstyle.font.bold = True
        hstyle.font.colour_index = 0x10             # dark red

        # for data
        dstyle = pyExcelerator.XFStyle ()
        dstyle.font.name = "Arial"
        dstyle.font.bold = False
        dstyle.font.colour_index = 0x27              # dark blue

        # for all tests performed in this instance
        for itest in self._tests:

            # check whether this test was performed or not
            if (itest not in self._p):
                continue

            # create the excel page
            ws = wb.add_sheet ("%s - %s" % (TESTS [itest], self._name))

            # create the panes splitters
            ws.panes_frozen = True
            ws.horz_split_pos = 2
            ws.vert_split_pos = 2

            # compute the headers - show the names of all series
            row=1
            col=2
            for iserie in self._series:
                ws.write (row, col, iserie, hstyle)
                col += 1

            # now, start adding data rows
            row += 1
            col = 2
            for iserie in self._series:
                ws.write (row, 1, iserie, hstyle)
                for jserie in self._series:
                    if (iserie != jserie):
                        ws.write (row, col, self._p [itest][iserie][jserie], dstyle)
                    else:
                        ws.write (row, col, '---', dstyle)
                    col +=1
                row += 1
                col = 2

            # and finally show the footer
            row += 2
            col = 2
            ws.write (row, col, TESTS [itest])
            col += 1
            lines = DESCS [itest].split ('\n')
            for iline in lines:

                ws.write (row, col, "%s" % iline)
                row += 1

            col = 2
            row += 1
            ws.write (row, col, " created by IPCrun %s (%s), %s" % (__version__, __revision__ [1:-2],
                                                                    datetime.datetime.now ().strftime ("%c")))

        # save the excel page, in case any has been used
        wb.save ("test.xls")

        # there is nothing particular to print here, so that return just the
        # empty string
        return (" File 'test.xls' has been generated")


    # print the contents of this class in wiki markup lang
    def print_wiki (self):
        """
        print the contents of this class in wiki markup lang
        """

        # initialization
        sout = ''

        # for all the statistical tests requested
        for itest in self._tests:

            # check whether this test was performed or not
            if (itest not in self._p):
                continue

            # print out the name of the table
            sout += "name: ''%s''" % self._name

            # compute the headers - show the names of the series
            sout += "\n|| ||"
            for iserie in self._series:
                sout += " '''%s''' ||" % iserie

            # now, start adding data rows
            for iserie in self._series:
                sout += "\n|| '''%s''' ||" % iserie
                for jserie in self._series:
                    if (iserie != jserie):
                        sout += "  %s ||" % self._p [itest][iserie][jserie]
                    else:
                        sout += "  --- ||"

            # show the footer
            sout += "\n  .  %s: %s" % (TESTS [itest], DESCS [itest].replace ("\n", ''))

            # and finally show the footer
            sout += "\n''created by IPCtest %s (%s), %s''\n" % (__version__, __revision__ [1:-2], 
                                                                datetime.datetime.now ().strftime ("%c"))

        # and return the string computed so far
        return sout        


# -----------------------------------------------------------------------------
# Handlers
#
# The following functions work just as handlers for extending the functionality
# of this module
# -----------------------------------------------------------------------------

# Statistical tests
#
# the following handlers shall return a list whose second item shall return the
# p-value that results of the statistical analysis
# -----------------------------------------------------------------------------

# Mann-Whitney U statistical test
def do_mw (seriea, serieb):
    """
    mann-whitney U statistical test. It returns the U statistics
    and the p-value ---to multiply by two in case of two-sided
    hypothesis
    """

    return scipy.stats.mannwhitneyu (seriea, serieb)


# T-test
def do_tt (seriea, serieb):
    """
    T-test. It returns the t-statistic and the two-tailed p-value
    """

    return scipy.stats.ttest_ind (seriea, serieb)


# Wilcoxon signed-rank test
def do_wx (seriea, serieb):
    """
    Wilcoxon signed-rank test. It returns the z-statistic and the two-tailed
    p-value
    """

    return scipy.stats.wilcoxon (seriea, serieb)


# Binomial two-tailed sign test
def do_bt (seriea, serieb):
    """
    Binomial two-tailed sign test. It returns the probability that the times the
    first serie is larger to the second follows a binomial distribution with
    p=.5
    """

    # first, compute n, the number of observations where seriea and serie b
    # differ
    n = reduce (lambda x,y:x+y,
                map (lambda x,y:1-int (x==y), seriea, serieb))
    
    # now, compute the number of times when seriea has a value which is larger
    # (and this is usually read as being "inferior", e.g., total-cost) to the
    # value in serieb
    k = reduce (lambda x,y:x+y,
                map (lambda x,y:int (x>y), seriea, serieb))

    # create a binomial distribution with n trials and probability .5
    binomial = scipy.stats.binom (n, .5)
    
    # and return the probability that at least k positive outcomes are obtained
    # in n trials ---it is returned in the second position as requested above
    return (0., 1. - binomial.cdf (k-1))


# Checkers
#
# the following handlers shall return true if the data passed is *expected* to
# be processed by the corresponding statistical test. Note that scipy library
# can still issue other warning/error messages when performing a particular test
#
# these are no longer in use since now exceptions raised by scipy are properly
# handled and the message is shown in the resulting tables. Nevertheless, they
# are kept here (along with their invocation) in case they are ever of use
# -----------------------------------------------------------------------------

# returns True if the series are *expected* to be correct for the Mann-Whitney U
# statistical test
def check_mw (series):
    """
    returns True if the series are *expected* to be correct for the Mann-Whitney U
    statistical test
    """

    return True


# returns True if the series are *expected* to be correct for the T-Test
# statistical test
def check_tt (series):
    """
    returns True if the series are *expected* to be correct for the T-Test
    statistical test
    """

    return True


# returns True if the series are *expected* to be correct for the Wilcoxon
# Signed-Rank statistical test
def check_wx (series):
    """
    returns True if the series are *expected* to be correct for the Wilcoxon
    Signed-Rank statistical test
    """

    return True

    
# returns True if the series are *expected* to be correct for the binomial
# two-tailed signed test
def check_bt (series):
    """
    returns True if the series are *expected* to be correct for the binomial
    two-tailed signed test
    """

    return True



# Local Variables:
# mode:python
# fill-column:80
# End:
