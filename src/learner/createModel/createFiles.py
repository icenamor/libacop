#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__      = "Isabel Cenamor"
__copyright__   = "Copyright 2013, Portfolio Project Features"
__email__ = "icenamor@inf.uc3m.es"

import sys
import string
import os

##translateFile --> translate
##features.arff --> preprocess
##initfeature-info.txt --> ff-learner
##tmp_results --> heuristics
def readFile(name, datos):
	print name
	fd = open(name,'r')
	datos = fd.readlines()
	fd.close()
	return datos

def writeFile(name, data, output):
	lineasLeidas = []
	fd = open(name,'w')
	d = 0
	while(data[d].find("@data") < 0):
		fd.write(data[d])
		d += 1
	fd.write("@attribute planner {arvand, dae_yahsp, fd-autotune-1, fd-autotune-2, fdss-1, fdss-2, lama-2008, lama-2011, lamar, lpg, madagascar, probe, randward, sgplan, yahsp2-mt}\n")
	fd.write("@attribute domain_output string\n")
	fd.write("@attribute problem_output numeric\n")
	fd.write("@attribute value numeric\n")
	fd.write("@attribute time numeric\n")
	fd.write("@attribute class {True, False}\n")
	fd.write(data[d])
	print (len(data)-d-1), len(output)
	number_repe = (len(output)/(len(data)-d-1))
	print number_repe
	repes = []
	while (number_repe > 0):
		ini = d + 1
		while (ini < len(data)):
			repes.append(data[ini])
			ini += 1
		number_repe -= 1
	print number_repe, len(repes)
	
	for inp, out in zip(repes,output):
		line = str(inp[:-1]) + "," + str(out)
		fd.write(line)
	fd.close()
	
def join(translate, preprocess, fflearner, heuristics, union):
	return union
# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    if (len(sys.argv) == 4):
    	
   	input_file = []
   	output_file = []
   	input_file = readFile(sys.argv[1], input_file)
   	output_file = readFile(sys.argv[2], output_file)
   	print len(input_file), len(output_file)
   	writeFile(sys.argv[3], input_file, output_file)
    else:
        print "ERROR:::: Need one argument to create the features file" 
        print "./createFiles.py <input_atributes> <output_attributes> <join_file>"
        sys.exit(-1)

