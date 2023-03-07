#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__      = "Isabel Cenamor"
__copyright__   = "Copyright 2014, Portfolio Project"
__email__ = "icenamor@inf.uc3m.es"


# imports
# -----------------------------------------------------------------------------
import os               # path and process management
import sys              # argv, exit

TIME_LIMIT = 900
MEMORY_LIMIT = 4096

# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    planners = ["seq-sat-arvand", "seq-sat-dae_yahsp", "seq-sat-fd-autotune-1", "seq-sat-fd-autotune-2", "seq-sat-fdss-1",
            "seq-sat-fdss-2", "seq-sat-lama-2008", "seq-sat-lama-2011", "seq-sat-lamar", "seq-sat-lpg", "seq-sat-madagascar",
            "seq-sat-probe", "seq-sat-randward", "seq-sat-sgplan", "seq-sat-yahsp2-mt"]
            
    # Check params
    if len(sys.argv) == 7:

        for i in xrange(1, 7, 2):

            if(sys.argv[i] == "-o"):
                if (os.path.isfile(sys.argv[i+1])):
                    domain_file = os.path.abspath(sys.argv[i+1])
                else:
                    print >> sys.stderr, "The domain file \"" + sys.argv[i+1] + "\" does not exists."
                    sys.exit(-1)

            elif(sys.argv[i] == "-t"):
                if (os.path.isdir(sys.argv[i+1])):
                    training_folder = os.path.abspath(sys.argv[i+1])
                else:
                    print >> sys.stderr, "The training folder \"" + sys.argv[i+1] + "\" does not exists."
                    sys.exit(-1)

            elif(sys.argv[i] == "-k"):
                dck_folder = os.path.abspath(sys.argv[i+1])

            else:
                print >> sys.stderr, "Error: unexpected parameter: " + sys.argv[i]
                sys.exit(-1)

    else:
        raise SystemExit("Usage: %s -o <domain file> -t <training folder> -k <DCK folder>" % sys.argv[0])
        sys.exit(-1)


    # Print params
    print "\nDomain file: " + domain_file
    print "Training folder: " + training_folder
    print "DCK folder: " + dck_folder + "\n"

    problems = os.listdir(training_folder)
    # Getting root path
    pathname = os.path.dirname(sys.argv[0])
    currentpath = os.path.abspath(pathname)
    rootpath = os.path.abspath(os.path.join(currentpath,".."))
    ##Features
    for problem in problems:	
        print "Extract Features with original problem and domain"
        ##print  rootpath + "/features/translate/translate.py"
        command = "python2.7 " + rootpath + "/features/translate/translate.py " + domain_file + " " + training_folder + "/"+ problem
	print "Run command: " + str(command)
	os.system(command)
	command =  rootpath + "/features/preprocess/preprocess < output.sas"
	print "Run command: " + str(command)
	os.system(command)
	command = rootpath + "/features/ff-learner/roller3.0 -o " + domain_file + " -f " +  training_folder + "/"+ problem + " -S 28 > init-features.txt"
	print "Run command: " + str(command)
	os.system(command)
	command = rootpath + "/features/heuristics/training.sh "  + domain_file + " "  +  training_folder + "/"+  problem
	print "Run command: " + str(command)
	os.system(command)
	actual_rootpath = rootpath + "/models"
	root_files = rootpath[:rootpath.rfind("/")]
	root_files = root_files[:root_files.rfind("/")+1]
	command = "python2.7 "+ actual_rootpath + "/joinFile.py " + root_files
	print "Run command: " + str(command)
	os.system(command)
    command = "java -cp "+ rootpath +"/models/weka.jar -Xmx2048M weka.filters.unsupervised.attribute.Remove -R 1,4,6,8-12,14-15,17-20,22,24-25,27-32,34-35,37,39-42,45-48,51-53,56-57,60-69,71-76,78-79,81,88-89,101-104 -i global_features.arff -o global_features_simply_clasification.arff"
    print "Run command: " + str(command)
    os.system(command)
    command = "java -cp "+ rootpath +"/models/weka.jar -Xmx2048M weka.filters.unsupervised.attribute.Remove -R 1-3,6,8,10-14,16-17,19-22,24,26-27,29-34,36-37,39,41-44,47-52,55-59,62-71,73-79,82-83,85,92-93,101-103,105 -i global_features.arff -o global_features_simply_regression.arff"
    print "Run command: " + str(command)
    os.system(command)
    #Create Models
    command = "java -Xmx1024M -cp "+ rootpath +"/Models/weka.jar weka.classifiers.rules.DecisionTable -t "+  rootpath +"/global_features_simply_regression.arff  -no-cv -d rules.DecisionTable.time.model"
    print "Run command: " + str(command)
    os.system(command)
    command = "java -Xmx1024M -cp "+ rootpath +"/Models/weka.jar weka.classifiers.trees.RandomForest -t "+  rootpath +"/global_features_simply_clasification.arff  -no-cv -d trees.RandomForest.model"
    
    print "Run command: " + str(command)
    os.system(command)
    command = "mv *.model " + dck_folder
    print "Run command: " + str(command)
    os.system(command)
    command = "mv *.arff " + dck_folder
    print "Run command: " + str(command)
    os.system(command)


    # Launching each candidate planner with every training problem
    command = "python2.7 invokeplanner.py "

    for i in planners:
        planner_path = rootpath + "/" + i
        command += " --planner " + planner_path + " "
    command += " -D " + domain_file + " -t " + training_folder + " --timeout " + str(TIME_LIMIT) + " --memory 4 -l ./logfile"

    os.chdir(rootpath + "/invoke-planner/")

    if(os.path.isdir(rootpath + "/invoke-planner/results")):
        print "\nThe results folder already exists, so we remove it.\n"
        os.system("rm -rf " + rootpath + "/invoke-planner/results")

    os.system(command)


    # Validating all the generated plans
    print "\nValidating all generated plans...\n"
    command = "python2.7 validate.py -d ./results"
    os.system(command)


    # Generating IPC report
    print "\nGenerating report\n"
    os.chdir(rootpath)

    if (os.path.isfile("./report.txt")):
        print "\nThe report file already exists, so we remove it\n"
        command = "rm ./report.txt"
        os.system(command)

    command = "python2.7 ./report/report.py --directory ./invoke-planner/results/ --level problem -v values oktimesols > ./report.txt"
    os.system(command)
    # Generating data for scip
    print "Creating file Results"
    ./output.py <IPC_results> file_output>"
    command = "python2.7 ./getResultsIPC/output.py report.txt outputArff"
    os.system(command)
    
    # Parsing the scip output and Generating dck file
    print "\nGenerating dck file...\n"
    domain_name = domain_file[domain_file.rfind("/") + 1: domain_file.rfind(".")]

    if(os.path.isdir(dck_folder)):
        if(os.path.isdir(dck_folder + "/" + domain_name)):
            print "\nThe folder " + dck_folder + "/" + domain_name + " already exists, so we remove it.\n"
            command = "rm -rf " + dck_folder + "/" + domain_name
            os.system(command)

        command = "mkdir " + dck_folder + "/" + domain_name
        os.system(command)

    else:
        print "\nDCK folder does not exist, we create it.\n"
        command = "mkdir " + dck_folder
        os.system(command)
        command = "mkdir " + dck_folder + "/" + domain_name
        os.system(command)


   

# Local Variables:
# mode:python2.7
# fill-column:80
# End:


