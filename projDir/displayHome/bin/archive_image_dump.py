#!/usr/bin/env python3.6

import argparse
import sys
import os
from datetime import datetime
import subprocess
import shutil
import time
from stat import *
import netCDF4

def timeString2DateTime(time_string):
    year = time_string[0:4]
    month = time_string[4:6]
    day = time_string[6:8]
    hour = time_string[8:10]
    minute = time_string[10:12]
    second = 0

    return datetime(int(year),
                    int(month),
                    int(day),
                    int(hour),
                    int(minute),
                    int(second))

def getMdvTimes(directory, start_time, end_time, filename_debug):

    stack = [directory]
    times = []

    while stack:
        directory = stack.pop()

        date_of_data = os.path.basename(directory)

        year = date_of_data[0:4]
        month = date_of_data[4:6]
        day = date_of_data[6:8]

        # cfrad.20190308_105505.000_to_20190308_105809.000_9355MWA_XXX.nc
        for file in os.listdir(directory):

            fullname = os.path.join(directory, file)
            basename = os.path.basename(file)

            if os.path.isdir(fullname) and not os.path.islink(fullname):
                if len(file.split("/")[-1]) == 8:
                    stack.append(fullname)
                continue

            extension = file.split(".")[-1]
            if extension != "mdv":
                continue

            hour = file[0:2]
            minute = file[2:4]
            second = file[4:6]

            if filename_debug:
                print("PROCESSING:", file, "Under directory", directory.split("/")[-1])

            this_time = datetime(int(year),
                                 int(month),
                                 int(day),
                                 int(hour),
                                 int(minute),
                                 int(second))

            if this_time >= start_time and this_time <= end_time:
                times.append( this_time )
                print("Adding time", this_time.strftime("%Y%m%d %H%M%S"))

    times.sort()
    return times

def main(arguments):

    parser = argparse.ArgumentParser(description="Archive MRRD data to a new location.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('start_time', help= "A required start time YYYYMMDDHHMM", type=str)
    parser.add_argument('end_time', help= "A required end time YYYYMMDDHHMM", type=str)
    parser.add_argument('CIDD_pfile', help= "A required CIDD parameter file name.", type=str)
    parser.add_argument('-source_directory', help= "Path to the data. Defaults to /home/nowcast/data/lakevic/mdv/satellite/meteosat-11.", type=str, default="/home/nowcast/data/lakevic/mdv/satellite/meteosat-11")
    parser.add_argument('-debug', help= "Turn on debug messages", action="store_true")
    parser.add_argument('-filename_debug', help= "Prints file names that are found processed.", action="store_true")

    args = parser.parse_args()

    if not os.path.exists(args.source_directory):
        print("ERROR: No Such directory", args.source_directory)
        sys.exit(-1)

    start_time = timeString2DateTime(args.start_time)
    end_time = timeString2DateTime(args.end_time)

    if args.debug:
        print("Archive start time:", start_time.strftime("%Y%m%d %H:%M"))
        print("Archive end time:", end_time.strftime("%Y%m%d %H:%M"))


    os.chdir(args.source_directory)

    if args.debug:
        print()
        print("chdir", args.source_directory)

    if args.debug:
        print("Compiling list of mdv files found for this time range.")
        print()

    mdv_times = getMdvTimes(args.source_directory, start_time, end_time, args.filename_debug)

    os.chdir(os.environ["DISPLAY_HOME"] + "/params")
    os.environ["DISPLAY"] = ":99"

    for this_time in mdv_times:

        # dump the image
        print()
        print("CIDD -p", args.CIDD_pfile, "-t", this_time.strftime("%Y%m%d%H%M"))
        subprocess.call(["CIDD", "-p", args.CIDD_pfile, "-t", this_time.strftime("%Y%m%d%H%M")])
        time.sleep(5)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
