#!/usr/bin/python

import sys
import os
import shutil
import getopt
from os.path import join, getsize

def print_usage():
    print
    print "Recursively Searches for a directory or file called searchDir "
    print "under dir and renames it to nameStr."
    print
    print "Usage: ", prog_name, " [options]"
    print "Options:"
    print "   -h | --help     : Print usage and exit"
    print "   --dir           : directory to start from"
    print "   --searchDir     : name of directory to be renamed"
    print "   --renameStr     : new name of directory\n"

prog_name = os.path.basename(sys.argv[0])
#
# Get the command line arguments.
#

optlist, args = getopt.getopt(sys.argv[1:], 'dh', \
                              [ 'help', \
                                'dir=',
                                'searchDir=',
                                'renameStr=', ])
# set command line defaults
# use "" if defaults are not perfered
search_string = ""
search_file = ""
directory = ""

for opt in optlist:
    if opt[0] ==  "-h" or opt[0] == "--help":
        print_usage()
        sys.exit()
    if opt[0] == "--dir":
        directory = opt[1]
    if opt[0] == "--searchDir":
        search_string = opt[1]
    if opt[0] == "--renameStr":
        new_name = opt[1]

if search_string is "" or directory is "" or new_name is "":
    print_usage()
    sys.exit()

directory = "./QPE"
for root, dirs, files in os.walk(directory):
    for name in dirs:
        if name == search_string:
            print >> sys.stderr, "mv", root + "/" + name + " " + root + "/" + new_name
            shutil.move(root + "/" + name, root + "/" + new_name)

sys.exit()
