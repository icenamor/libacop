#!/usr/bin/python2.7

from pyparsing import OneOrMore, nestedExpr
import os
import sys
import collections

# -----------------------------------------------------------------------------
# list_to_pddl
#
# Devuelve la lista "element" en formato pddl.
# -----------------------------------------------------------------------------
def list_to_pddl(element):
    text = ""

    if(isinstance(element, basestring)):
        text += element + " "

    else:
        text += "( "

        for i in element:
            if(isinstance(i, basestring)):
                text += i + " "
            else:
                text += list_to_pddl(i)

        text += ") "

    return text


# -----------------------------------------------------------------------------
# clean_problem_typing
#
# -----------------------------------------------------------------------------
def clean_problem_typing(original_problem, modified_problem):
    text = ""

    # Leemos el problema, lo almacenamos en un string y quitamos comentario
    pddl_lines = open(original_problem, 'r').readlines()

    for line in pddl_lines:

        if((len(line) > 0) and (line[len(line)-1] == '\n')):
            line = line[:-1] + " "	# Quitamos el \n

        line = line.lower()		# Todo a minuscula
        begin = line.find(";")		# Buscamos comentarios en la linea

        if(begin >= 0):			# Quitamos los comentarios de la linea
            line = line[0:begin]

        text += line


    # Parseamos el conetenido del pddl
    data = OneOrMore(nestedExpr()).parseString(text)

    if(len(data) == 1):

        # Creamos el fichero de salida
        new_file = open(modified_problem, 'w')
        new_file.write("(")

        for element in data[0]:

            if(element[0] == ":requirements"):
                requirements = "( "
                for req in element:

                    if(req != ":typing"):
                        requirements += req + " "

                requirements += " )"
                if (len(requirements.split()) > 3):
                    new_file.write(requirements + "\n")

            else:
                new_file.write(list_to_pddl(element) + "\n")

        new_file.write(")")
        new_file.close()

    else:
        sys.exit(-1)



# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) != 3:
        raise SystemExit("Usage: %s <INPUT_PROBLEM_FILE> <OUTPUT_PROBLEM_FILE>" % sys.argv[0])

    else:
        # Calculamos la ruta absoluta del script
        pathname = os.path.dirname(sys.argv[0])
        scriptpath = os.path.abspath(pathname)

        if (os.path.isfile(sys.argv[1])):
            input_problem_file = os.path.abspath(sys.argv[1])
            output_problem_file = os.path.abspath(sys.argv[2])

        else:
            print("The problem file does not exist: %s \n" % sys.argv[1])
            sys.exit(-1)

        print "\nRemoving typing requeriment...\n\n"
        print "Input Problem file: " + input_problem_file
        print "Output Problem file: " + output_problem_file + "\n"
        clean_problem_typing(input_problem_file, output_problem_file)


