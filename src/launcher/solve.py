#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__      = "Isabel Cenamor"
__copyright__   = "Copyright 2014, Learning Portfolio Project"
__email__ = "icenamor@inf.uc3m.es"

# imports
# -----------------------------------------------------------------------------
import os               # path and process management
import resource         # process resources
import shutil           # copy files and directories
import signal           # process management
import sys              # argv, exit
import time             # time mgmt

import systools         # IPC process management
import timetools        # IPC timing management
import math

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------

CHECK_INTERVAL = 5           # how often we query the process group status
KILL_DELAY = 5               # how long we wait between SIGTERM and SIGKILL


# -----------------------------------------------------------------------------

# constants
# -----------------------------------------------------------------------------

optimal_planning = False
cleaned_plan_file = "cleaned_result.result"


# -----------------------------------------------------------------------------

# funcs
# -----------------------------------------------------------------------------

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
        print ("c %s in 'set_limit'" % e)


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
# run
#
# Time is measured in seconds and memory in bytes
#
# -----------------------------------------------------------------------------
def run (script, domain, problem, plan_sol, timeout, memory):
    global counter
    global best_cost

    # create a timer
    runtimer = timetools.Timer ()

    # Now, a child is created which will host the planner execution while this
    # process simply monitors the resource comsumption. If any is exceeded the
    # whole process group is killed
    with runtimer:

        child_pid = os.fork()
        if not child_pid:                                            # child's code
            os.setpgrp()
            set_limit(resource.RLIMIT_CPU, timeout)
            set_limit(resource.RLIMIT_AS, memory)
            set_limit(resource.RLIMIT_CORE, 0)
            os.execl(script, script, domain, problem, plan_sol)

        real_time = 0
        while True:
            time.sleep(CHECK_INTERVAL)
            real_time += CHECK_INTERVAL

            data = os.system("ls -l " + plans_folder + "/" + cleaned_plan_file + "* > /dev/null 2>&1")
            if(data == 0):
                # Move plan files to the specific folder/name provided by the IPC software
                data = os.popen("ls -l " + plans_folder + "/" + cleaned_plan_file + "*")
                for line in data.readlines():
                    if((len(line) > 0) and (line[len(line)-1] == '\n')):
                        line = line[:-1].strip()		# Quitamos el \n

                    elements = line.split()

                    if(len(elements) > 0):
                        name = elements[len(elements)-1].strip()
                        print "Name: " + str(name)

                        # Validate the current plan file to get the plan cost
                        command = rootpath + "/parser/VAL-4.2.08/validate -v " + original_domain_file + "  " + original_problem_file + " " + name
                        val_data = os.popen(command)
                        successful_plan = False
                        current_cost = -1

                        for val_line in val_data.readlines():
                            val_line = val_line.strip()
                            if((len(val_line) > 0) and (val_line[len(val_line)-1] == '\n')):
                                val_line = val_line[:-1]		# Quitamos el \n

                            if(val_line.find("Successful plans:") >= 0):
                                successful_plan = True

                            elif(val_line.find("Value:") >= 0):
                                cost_elements = val_line.split()
                                if(len(cost_elements) == 2):
                                    current_cost = int(cost_elements[1].strip())
                                else:
                                    print "ERROR! Wrong cost line: " + str(val_line)

                        if((not successful_plan) or (current_cost == -1)):
                            print("Warning: Plan " + str(name) + " is not valid or the plan cost is equal to -1, therefore we remove it")
                            os.system("rm -f " + name)

                        elif((counter == 1) or (current_cost < best_cost)):
                            best_cost = current_cost
                            print "New best plan cost found: " + str(best_cost)
                            command = "mv " + name + " " + original_plan_file + "." + str(counter)
                            print "Run command: " + str(command)
                            os.system(command)
                            counter += 1

                        else:
                            print("Warning: El plan " + str(name) + " is worse (" + str(current_cost) + ") than the previous plan generated (" + str(best_cost) + "), therefore we remove it")
                            os.system("rm -f " + name)


            group = systools.ProcessGroup(child_pid)

            # Generate the children information before the waitpid call to avoid a
            # race condition. This way, we know that the child_pid is a descendant.
            if os.waitpid(child_pid, os.WNOHANG) != (0, 0):
                break

            # get the total time and memory usage
            process_time = real_time
            total_time = group.total_time()

            # if multicore ain't enabled, the usual rules apply
            try_term = (total_time >= timeout or
                        real_time >= 1.5 * timeout)
            try_kill = (total_time >= timeout + KILL_DELAY or
                        real_time >= 1.5 * timeout + KILL_DELAY)

            term_attempted = False
            if try_term and not term_attempted:
                print ("c aborting children with SIGTERM...")
                print ("c children found: %s" % group.pids())
                kill_pgrp(child_pid, signal.SIGTERM)
                term_attempted = True
            elif term_attempted and try_kill:
                print ("c aborting children with SIGKILL...")
                print ("c children found: %s" % group.pids())
                kill_pgrp(child_pid, signal.SIGKILL)

        # Even if we got here, there may be orphaned children or something we may
        # have missed due to a race condition. Check for that and kill.
        group = systools.ProcessGroup(child_pid)
        if group:
            # If we have reason to suspect someone still lives, first try to kill
            # them nicely and wait a bit.
            print ("c aborting orphaned children with SIGTERM...")
            print ("c children found: %s" % group.pids())
            kill_pgrp(child_pid, signal.SIGTERM)
            time.sleep(1)

        # Either way, kill properly for good measure. Note that it's not clear if
        # checking the ProcessGroup for emptiness is reliable, because reading the
        # process table may not be atomic, so for this last blow, we don't do an
        # emptiness test.
        kill_pgrp(child_pid, signal.SIGKILL)

    return real_time


# -----------------------------------------------------------------------------
# run_portfolio
#
# Run each planner with its allotted time 
#
# -----------------------------------------------------------------------------
def run_portfolio (planners, timeouts, memory):

    accumulated_time = 0

    print "\nOriginal_Domain: " + str(original_domain_file)
    print "Original_Problem: " + str(original_problem_file)
    print "Domain_wac: " + str(domain_file_wac)
    print "Problem_wtp: " + str(problem_file_wtp)
    print "Problem_wtp_and_wac: " + str(problem_file_wtp_and_wac)
    print "Original_Plan_file: " + str(original_plan_file)
    print "Plans folder: " + str(plans_folder) + "\n"


    for i in xrange(0, len(planners)):
        # Configuring planner path
        planner = rootpath + "/" + planners[i] + "/plan"
        timeout = timeouts[i]

        print "\n\n****************************************************"
        print "*** Planner_path: " + planner + " TimeOut: " + str(timeout) + " ***"
        print "****************************************************\n\n"

        result = plans_folder + "/" + cleaned_plan_file
        if((planner.find("lpg") >= 0) or (planner.find("sgplan") >= 0)):
            executed_time = run (planner, domain_file_wac, problem_file_wtp_and_wac, result, timeout, memory)
            print "Planner " + planner + " run " + str(executed_time) + " seconds\n"
            accumulated_time += executed_time

        else:
            executed_time = run (planner, original_domain_file, problem_file_wtp, result, timeout, memory)
            print "Planner " + planner + " run " + str(executed_time) + " seconds\n"
            accumulated_time += executed_time


        # If we are in optimal planning and the optimal solution was found, we finish the execution
        if((counter > 1) and (optimal_planning)):
            break

    return accumulated_time
    
def readFile(data, name):
	fd = open(name,'r')
	data2 = []
	data2 = fd.readlines()
	fd.close()
	for i in data2:
	    data.append(i[:-1])
	return data

# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    memory   = 4241280205 # 3,95 GB
    timelimit = 900
    best_cost = -1
    counter = 1
    knowledge = False
    planners = []
    timeouts = []
    planners_d = [ "yahsp2-mt",  "randward", "arvand", "fd-autotune-1","lama-2008", "probe", "madagascar", "lpg", "fdss-1", "lama-2011",  "fd-autotune-2", "fdss-2", "lamar" , "sgplan", "dae_yahsp"]
    timeouts_d = [60,60,60,60,60,60,60,60,60,60,60,60,60,60,60]

    # Check params
    if len(sys.argv) == 7 or len(sys.argv) == 9:

        for i in xrange(1, len(sys.argv), 2):

            if(sys.argv[i] == "-o"):
                if (os.path.isfile(sys.argv[i+1])):
                    original_domain_file = os.path.abspath(sys.argv[i+1])
                else:
                    print >> sys.stderr, "The domain file \"" + sys.argv[i+1] + "\" does not exists."
                    sys.exit(-1)

            elif(sys.argv[i] == "-f"):
                if (os.path.isfile(sys.argv[i+1])):
                    original_problem_file = os.path.abspath(sys.argv[i+1])
                else:
                    print >> sys.stderr, "The problem file \"" + sys.argv[i+1] + "\" does not exists."
                    sys.exit(-1)

            elif(sys.argv[i] == "-k"):
                if (os.path.isdir(sys.argv[i+1])):
                    knowledge = True
                    dck_folder = os.path.abspath(sys.argv[i+1])
                    print "\nRunning with knowledge...\n"
                else:
                    print >> sys.stderr, "The dck folder \"" + sys.argv[i+1] + "\" does not exists."
                    sys.exit(-1)

            elif(sys.argv[i] == "-p"):
                original_plan_file = sys.argv[i+1]

            else:
                print >> sys.stderr, "Error: unexpected parameter: " + sys.argv[i]
                sys.exit(-1)

    else:
        raise SystemExit("Usage: %s -o <domain_file> -f <problem_file> -p <plan_file> [-k <DCK_folder>]" % sys.argv[0])
        sys.exit(-1)

    begin = time.time()
    print "\nDomain file: " + original_domain_file
    print "Problem file: " + original_problem_file
    if(knowledge):
        print "DCK folder: " + dck_folder
    print "Plan file: " + original_plan_file + "\n"


    # Getting root path
    pathname = os.path.dirname(sys.argv[0])
    currentpath = os.path.abspath(pathname)
    rootpath = os.path.abspath(os.path.join(currentpath,"..")) 
    # Loading knowledge
    if(knowledge):
        print "Extract Features with original problem and domain"
        command = "python2.7 " + rootpath + "/features/translate/translate.py " + original_domain_file + " " + original_problem_file
        print "Run command: " + str(command)
        os.system(command)
        command =  rootpath + "/features/preprocess/preprocess < output.sas"
        print "Run command: " + str(command)
        os.system(command)
        command = rootpath + "/features/ff-learner/roller3.0 -o " + original_domain_file + " -f " + original_problem_file + " -S 28"
        print "Run command: " + str(command)
        os.system(command)
        command = rootpath + "/features/heuristics/training.sh "  + original_domain_file + " " + original_problem_file
        print "Run command: " + str(command)
        os.system(command)
        actual_rootpath = rootpath + "/models"
        command = "python2.7 "+ actual_rootpath + "/joinFile.py " + rootpath[:rootpath.rfind("/")+1] + " \n"
        print "Run command: " + str(command)
        
        os.system(command)
        command = "java -cp "+ rootpath +"/models/weka.jar -Xmx2048M weka.filters.unsupervised.attribute.Remove -R 1-3,6,8,10-14,16-17,19-22,24,26-27,29-34,36-37,39,41-44,47-52,55-59,62-71,73-79,82-83,85,92-93 -i global_features.arff -o global_features_simply.arff"
        print "Run command: " + str(command)
        os.system(command)
        ##java -Xmx1024M -cp models/weka.jar weka.classifiers.trees.J48 -l models/generalJ48.model -T global_features_simply.arff -p 96 > models/outputModel
        command = "java -Xmx1024M -cp "+ rootpath +"/models/weka.jar weka.classifiers.trees.RandomForest -l "+ dck_folder +"/trees.RandomFores.model -T global_features_simply.arff -p 35 > outputModel"
        print "Run command: " + str(command)
        os.system(command)
        ## python models/parseWekaOutputFile.py models/outputModel models/listPlanner
        command = "python2.7 "+ rootpath +"/models/parseWekaOutputFile.py outputModel listPlanner"
        print "Run command: " + str(command)
       	os.system(command)
       	print "************ Start Regression **********************"
       	##pass classification to regression
       	actual_rootpath = rootpath + "/models"
        command = "python2.7 "+ actual_rootpath + "/joinFileRegression.py " + rootpath[:rootpath.rfind("/")+1] +" listPlanner\n"
        print "Run command: " + str(command)
       	os.system(command)
       	command = "java -cp "+ rootpath +"/models/weka.jar -Xmx2048M weka.filters.unsupervised.attribute.Remove -R 1-3,6,8,10-14,16-17,19-22,24,26-27,29-34,36-37,39,41-44,47-52,55-59,62-71,73-79,82-83,85,92-93 -i global_features_regression.arff -o global_features_simply_regression.arff"
        print "Run command: " + str(command)
       	os.system(command)
       	command = "java -Xmx1024M -cp "+ rootpath +"/models/weka.jar/ weka.classifiers.rules.DecisionTable  -l "+ dck_folder +"/rules.DecisionTable.model -T global_features_simply_regression.arff -p 35 > outputModelRegression"
        print "Run command: " + str(command)
        os.system(command)
        command = "python2.7 "+ rootpath +"/models/parseWekaOutputFileRegression.py outputModelRegression listPlannerRegression"
        print "Run command: " + str(command)
        os.system(command)
        planners_time = []
        planners_time = readFile(planners_time, "listPlannerRegression")
        for i in planners_time:
        	planner = i[:i.find(",")]
        	timer =  i[i.find(",")+1:]
        	planners.append(planner)
        	timeouts.append(int(timer))
    if(len(planners) == 0):
       	for planner, timer in zip(planners_d, timeouts_d):
       		planners.append(planner)
        	timeouts.append(int(timer))
        		
    print "\nPortfolio configuration:"
    for i in xrange(0, len(planners)):
        print "planner,time", planners[i] + " " + str(timeouts[i])


    ## Getting modified paths
    plans_folder = rootpath + "/plans_folder"
    problem_file_wtp = original_problem_file[:original_problem_file.rfind(".")] + "_wtp.txt"
    problem_file_wtp_and_wac = original_problem_file[:original_problem_file.rfind(".")] + "_wtp_and_wac.txt"
    domain_file_wac = original_domain_file[:original_domain_file.rfind(".")] + "_wac.txt"


    ## Checking if modified paths already exist. If so, we remove it
    if (os.path.isfile(problem_file_wtp)):
        print "\nThe temporal file " + problem_file_wtp + " already exists, so we remove it.\n"
        command = "rm -rf " + problem_file_wtp
        os.system(command)

    if (os.path.isfile(problem_file_wtp_and_wac)):
        print "\nThe temporal file " + problem_file_wtp_and_wac + " already exists, so we remove it.\n"
        command = "rm -rf " + problem_file_wtp_and_wac
        os.system(command)

    if (os.path.isfile(domain_file_wac)):
        print "\nThe temporal file " + domain_file_wac + " already exists, so we remove it.\n"
        command = "rm -rf " + domain_file_wac
        os.system(command)


    print "\nParsing problems...\n"
    ##os.chdir(rootpath + "/parser/")

    command = "python2.7 "+ rootpath +"/parser/clean_typing.py " + original_problem_file + " " + problem_file_wtp
    os.system(command)

    command = "python2.7 "+ rootpath + "/parser/clean_action_costs.py " + original_domain_file + " " + domain_file_wac + " " + problem_file_wtp + " " + problem_file_wtp_and_wac
    os.system(command)

    end = time.time()
    accumulated_time = end - begin
    accumulated_time = int(accumulated_time) + 1
    print "Parsers took " + str(accumulated_time) + " seconds\n"


    # run main portfolio
    accumulated_time += run_portfolio (planners, timeouts, memory)
    print "Main portfolio runs " + str(accumulated_time) + " seconds\n"

    # some planner failed, therefore there is remaining time. Run default planner
    if((accumulated_time < timelimit) and ((counter == 1) or ((counter > 1) and (not optimal_planning)))):
        planners = ["sgplan"]
        timeouts = [(timelimit - accumulated_time)]
        accumulated_time += run_portfolio (planners, timeouts, memory)
        print "Main portfolio plus default planner run " + str(accumulated_time) + " seconds (in total)\n"

        # It is very rare.. It is possible that all planners failed: memory or there is a problem with the original problem/domain. We run blind planner with original_data
        if((accumulated_time < timelimit) and ((counter == 1) or ((counter > 1) and (not optimal_planning)))):
            planners = ["blind"]
            timeouts = [(timelimit - accumulated_time)]
            original_data = True
            accumulated_time += run_portfolio (planners, timeouts, memory)
            print "Main portfolio plus default planner plus blind planner run " + str(accumulated_time) + " seconds (in total)\n"


# Local Variables:
# mode:python2.7
# fill-column:80
# End:


