#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__      = "Isabel Cenamor"
__copyright__   = "Copyright 2013, Portfolio Project Features"
__email__ = "icenamor@inf.uc3m.es"

import sys
import string
import os
from head import Head

##translateFile --> translate
##features.arff --> preprocess
##initfeature-info.txt --> ff-learner
##tmp_results --> heuristics
def readFile(name, datos):
	print name
	
	fd = open(name,'r')
	linea = fd.readline()
	while linea != "":
		datos.append(linea)
		linea = fd.readline()
	return datos

def writeFile(name, data, head):
	fd = open(name,'w')
	##lines = fd.readlines()
	for i in head.head:
		fd.write(i)
	line = ""
	for i in data:
		line = line + i
	entry = line + ",arvand,?\n"
	fd.write(entry)
	entry = line + ",fd-autotune-1,?\n"
	fd.write(entry)
	entry = line  + ",fd-autotune-2,?\n"
	fd.write(entry)
	entry = line  + ",fdss-1,?\n"
	fd.write(entry)
	entry = line  + ",fdss-2,?\n"
	fd.write(entry)
	entry = line  + ",lama-2008,?\n"
	fd.write(entry)
	entry = line + ",lama-2011,?\n"
	fd.write(entry)
	entry = line + ",madagascar,?\n"
	fd.write(entry)
	entry = line + ",lpg,?\n"
	fd.write(entry)
	entry = line + ",probe,?\n"
	fd.write(entry)
	entry = line + ",randward,?\n"
	fd.write(entry)
	entry = line + ",yahsp2-mt,?\n"
	fd.write(entry)
	entry = line + ",dae_yahsp,?\n"
	fd.write(entry)
	entry = line + ",lamar,?\n"
	fd.write(entry)
	entry = line + ",sgplan,?\n"
	fd.write(entry)
	fd.close()
	
def join(translate, preprocess, fflearner, heuristics, union):

	if(len(translate) > 0):
		union = union + translate[0]
	else:
		print "There is not translate"
		entry_translate = "?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?"
		union = union + entry_translate
	union = union + ","
	if(len(preprocess) > 0):
	
		union = union + preprocess[0][:len(preprocess[0])-1]
	else:
		print "There is not preprocess"
		entry_translate = "?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?"
		union = union + entry_translate
	union = union + ","
	if(len(fflearner) > 0):
	
		union = union + fflearner[0][:len(fflearner[0])-1]
	else:
		print "There is not fflearner"
		entry_translate = "?,?,?,?,?,?,?,?,?,?,?,?,?"
		union = union + entry_translate
	union = union + ","
	if(len(heuristics) > 0):

		union = union + heuristics[0][:len(heuristics[0])-1]
	else:
		print "There is not heuristics"
		entry_translate = "?,?,?,?,?,?,?,?,?"
		union = union + entry_translate
	return union
# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    translate = []
    preprocess =[]
    fflearner = []
    heuristics =[]
    union_final = ""
    route = ""
    if (len(sys.argv) == 2):
        route = sys.argv[1]
    else:
        print "ERROR:::: Need one argument to create the features file" 
        sys.exit(-1)
    try:
	    print route + "/translateFile"
	    translate = readFile(route+"/translateFile", translate) ## translateFile
	   
    except:
	    print "No file in translate"
	    translate = ["?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?"]
    try:
	    preprocess = readFile(route+"/features.arff", preprocess) ## features.arff
    except:
	    print "No file in preprocess"
	    preprocess = ["?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?\n"]
    try:
	    fflearner = readFile(route+"/initfeature-info.txt", fflearner) 
    except:
	    print "No file in fflearner"
	    fflearner = ["?,?,?,?,?,?,?,?,?,?,?,?,?\n"]
    try:
	    heuristics = readFile(route+"/tmp_results", heuristics)
    except:
	    print "No file in heuristics"
	    heuristics = ["?,?,?,?,?,?,?,?,?\n"]
    try:
	    union_final = join(translate, preprocess, fflearner, heuristics, union_final)
    except:
	    print "General error"
	    union_final = "?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?"
    head = Head([])
    writeFile(route+"/global_features.arff", union_final, head)
