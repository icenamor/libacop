#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sys
import string
import os
from ResultRegression import ResultRegression
from Result import Instance
from operator import itemgetter, attrgetter
ERROR = 1.6
STRATEGY = 5
TIME = 900


def readFile(data, name):
	fd = open(name,'r')
	data = fd.readlines()
	fd.close()
	return data

def clear_data(data):
	data2 = []
	i = 0
	start = 0
	while(i < len(data)):
		if(data[i].find("#") < 0 and start == 0):
			i = i + 1
		elif(data[i].find("#") > 0  and start == 0):
			i = i + 1
			start = 1
		else:
			start = 1
		if(start == 1):
			if(len(data[i]) > 1):
				data2.append(data[i])
		i = i + 1
	data = data2
	return data
	
	
def sorted_results(data, sortedData):
	maximun = 0
	for i in data:
		if(float(i.predicted) <= 1):
			i.predicted = 10
		maximun += (i.predicted*i.error)
	for i in data:
		value = int(TIME * (i.predicted*i.error) /maximun)
		i.predicted = value
		sortedData.append(i)
	return sortedData
	
	
def writeFile(sortedData, name, numberPlanner):
	fd = open(name, 'w')
	i = 0
	while(i < numberPlanner):
		planner = sortedData[i].planner
		time = sortedData[i].predicted
		fd.write(planner+","+str(time)+"\n")
		i = i + 1
	
	fd.close()

def split_problems(data, listData):
	n = 0
	aux = 1
	for i in data:
		if(aux < 6):
			listData[n].append(i)
			aux =  aux + 1
		else:
			listData[n].append(i)
			n = n + 1
			aux = 1
	return listData

if(len(sys.argv) >= 3):
	data = []
	data = readFile(data, sys.argv[1])
	data = clear_data(data)
	results = []
	for i in data:
		result = ResultRegression(0, "", "", 0.0, "")
		result = result.split_line(i)
		results.append(result)
	## from more than one problem
	listData = []
	for i in range(int(len(results)/5)):
		listData.append([])
	listData = split_problems(results, listData)
	list_aux = []
	for i in listData:
		for j in i:
			list_aux.append(j)
	sortedData = []
	sortedData = sorted_results(list_aux, sortedData)
	
	if(len(sys.argv) == 4):
		writeFile(sortedData, sys.argv[2], int(sys.argv[3]))
	else:
		writeFile(sortedData, sys.argv[2], STRATEGY)
		
else:
	print "Need python parseWekaOutputFile.py input input2"
	print "input >> output model"
	print "input >> domain,problem"
	sys.exit(-1)
