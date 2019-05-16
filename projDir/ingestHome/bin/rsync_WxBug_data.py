#!/usr/bin/python

###############################################################
# rsync_WxBug_data.py                                          #
###############################################################
# Python script for copying lightning files from atec-dataops #
# to winter                                                   #
###############################################################

import os
import getopt
import string
import sys
import time
import shutil
import subprocess as sub

###############################################################
# Local subroutines                                           #
###############################################################

###############################################################
# print_usage(): Print the usage for this script
#

def print_usage():
  print "Usage: ", prog_name, " [options]"
  print "   -h | --help                   : Print usage and exit"
  print "   -d | --debug                  : Print debug messages"
  print "   --date                        : date to process (default todays date)"
  print "   --input                       : default <hardt@atec-dataops:/raid/ext_obs/lightning>"
  print "   --output                      : defualt </d1/data/raw/lightning/Wxbug>\n"
  return

def get_date():
  this_time = time.time()
  time_tuple = time.gmtime( this_time )
  year = str(time_tuple[0])
  month = str(time_tuple[1])
  if time_tuple[1] < 10:
    month = "0" + month
  day = str(time_tuple[2])
  if time_tuple[2] < 10:
    day = "0" + day
  this_date = year + month + day
  return this_date

def get_previous_date():
  this_time = time.time() - 86400
  time_tuple = time.gmtime( this_time )
  year = str(time_tuple[0])
  month = str(time_tuple[1])
  if time_tuple[1] < 10:
    month = "0" + month
  day = str(time_tuple[2])
  if time_tuple[2] < 10:
    day = "0" + day
  this_date = year + month + day
  return this_date

def get_time():
#  this_time = time.time() - 86400
  this_time = time.time()
  time_tuple = time.gmtime( this_time )
  hour = str( time_tuple[3] )
  if time_tuple[3] < 10:
    hour = "0" + hour
  min = str( time_tuple[4] )
  if time_tuple[4] < 10:
    min = "0" + min
  this_time = hour + min
  return this_time

###############################################################
# Main program                                                #
###############################################################

if __name__ == "__main__":

  #
  # Retrieve the program name from the command line.
  #

  prog_name = os.path.basename(sys.argv[0])

  #
  # Initialize the command line arguments.
  #

  opt_date = ""
  opt_debug = 0
  opt_input = "hardt@atec-dataops:/raid/ext_obs/lightning"
  opt_output = "/d1/data/raw/lightning/Wxbug"
  
  optlist, args = getopt.getopt(sys.argv[1:], 'dhp', \
        [ 'help', \
          'date=',
          'input=',
          'output='
        ])

  for opt in optlist:
    
    if opt[0] == "-h" or opt[0] == "--help":
      print_usage()
      sys.exit()

    if opt[0] == "-d" or opt[0] == "--debug":
      opt_debug = 1

    if opt[0] == "--date":
      opt_date = opt[1]

    if opt[0] == "--input":
      opt_input = opt[1]

    if opt[0] == "--output":
      opt_output = opt[1]

  if opt_date == "":
    process_date = get_date()
  else:
    process_date = opt_date

  if opt_debug:
    print >> sys.stderr, "Processing date ", process_date

  if not os.path.exists(opt_output + "/" + process_date):
    os.mkdir(opt_output + "/" + process_date)

  #--- Only want to sync current days data into
  #--- a subdirectory with that date
  rsync_command =  "rsync -auv --chmod=ugo=rwX --include=\"" + process_date + "*\" --exclude=\"*\" " + opt_input + "/ "  + opt_output + "/" + process_date
  if opt_debug:
    print >> sys.stderr, rsync_command

  #--- Rsync the requested day
  d = sub.Popen(rsync_command, shell=True) 
  error_out = d.communicate()[1]
  if opt_debug:
    if error_out != " None ":
      print >> sys.stderr, "Error:", error_out, "-"

  #--- Rsync the precious day at the beginning of a new day
  current_time = int( get_time() )
  if current_time < 10:
    process_date = get_previous_date()
    if opt_debug:
      print >> sys.stderr, "Processing previous date of ", process_date
    if not os.path.exists(opt_output + "/" + process_date):
      os.mkdir(opt_output + "/" + process_date)
    if opt_debug:
      print >> sys.stderr, rsync_command
    d = sub.Popen(rsync_command, shell=True)
    error_out = d.communicate()[1]
    if opt_debug:
      if error_out != " None ":
        print >> sys.stderr, "Error:", error_out, "-"

  sys.exit()

