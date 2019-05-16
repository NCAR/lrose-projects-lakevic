#!/usr/bin/env python3

import sys
import os
import ftplib
import argparse
from datetime import datetime
from datetime import timedelta

def ftp_file(server, username, password, remote_path, local_filename, remote_filename):

    ftp_connection = ftplib.FTP(server, username, password)
    ftp_connection.cwd(remote_path)
    fh = open(local_filename, 'rb')
    ftp_connection.storbinary('STOR ' + remote_filename, fh)
    fh.close()

def find_closest_day(now, imageTime):

    td = timedelta(hours=24)
    back24 = now - td

    today = datetime(now.year, now.month, now.day, int(imageTime[0:2]), int(imageTime[2:4]), 0)
    yesterday = datetime(back24.year, back24.month, back24.day, int(imageTime[0:2]), int(imageTime[2:4]), 0)

    if now < today:
        return yesterday
    else:
        return today

def main(arguments):

    parser = argparse.ArgumentParser(description=
                                     "",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_file', help = "A required image file data file.", type=str)
    parser.add_argument("file_modify_time", help = "A required file modify time. Used to catch InputWatcher argument.", type=int)
    parser.add_argument('-debug', help= "Turn on debug messages", action="store_true")
    parser.add_argument('-test_mode', help= "Turn on test_mode. ftp not executed.", action="store_true")

    args = parser.parse_args(arguments)

    server = "catalog.eol.ucar.edu"
    username = "anonymous"
    password = "hardt@ucar.edu"
    remote_path = "pub/incoming/catalog/highway"

    filename = os.path.basename(args.input_file)
    filepath = os.path.dirname(args.input_file)

    # CH_satellite_METEOSAT11_10-8micron-5min-strike-accumulation_0.5_1602.png
    # CH_satellite_METEOSAT11_10-8micron-15min-strike-accumulation_0.5_1602.png
    # CH_surface_Africa-3DPAWS-TAHMO-GTS_wind-temperature-dewpoint_0.5_1602.png
    # CH_radar_Africa-ARC_mwanza-DBZ_0.5_1602.png

    # output format: category.platform.YYYYMMDDHHmm.product.png

    underscore_split = filename.split("_")
    dot_split = filename.split(".")

    image_HHMM = underscore_split[-1].split(".")[0]

    current_datetime = datetime.utcnow()
    image_datetime = find_closest_day(current_datetime, image_HHMM)

    category = underscore_split[1]
    platform = underscore_split[2].replace("-", "_")

    #
    # needed to fix the field name in CIDD which changed file name.
    # For the field Catalog the file names cant change so this
    # statement keeps the file names the same.
    #
    if platform == "Africa_3DPAWS_TAHMO_AWS":
        platform = "Africa_3DPAWS_TAHOMO_GTS"
        
    image_date = filepath.split("/")[-1]
    image_time_string = image_date + image_HHMM

    product = underscore_split[3].replace("-", "_")
    extension = dot_split[-1]

    remote_filename = category + "." + platform + "." + image_time_string + "." + product + "." + extension

    if args.debug:
        print()
        print("Server:", server)
        print("username:",username)
        print("password:", password)
        print("remote path:", remote_path)
        print("local file name:", args.input_file)
        print("remote file name:", remote_filename)


    if not args.test_mode:
        ftp_file(server, username, password, remote_path, args.input_file, remote_filename)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
