#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from datetime import timedelta
import math
import subprocess
import time
from glob import glob


def get_station_id_lat_lon_alt(location_file, station):

    lat = -9999
    lon = -9999
    alt = -9999
    id = 'unknown'

    inFile = open(location_file, 'r')
    lines = inFile.readlines()
    for line in lines:
        info = line.split()
        if info[0] == station:
            id = info[1]
            lat = float(info[2])
            lon = float(info[3])
            alt = float(info[4])

    return id, lat,lon, alt


def get_start_and_end_datetime_objects(requested_start, requested_end):

    year = requested_start[0:4]
    month = requested_start[4:6]
    day = requested_start[6:8]
    hour = requested_start[8:10]
    min = requested_start[10:12]
    start = datetime(int(year), int(month), int(day), int(hour), int(min), 0)

    eyear = requested_end[0:4]
    emonth = requested_end[4:6]
    eday = requested_end[6:8]
    ehour = requested_end[8:10]
    emin = requested_end[10:12]
    end = datetime(int(eyear), int(emonth), int(eday), int(ehour), int(emin), 0)

    return start,end


def get_days_in_time_inteval(start_time, end_time):

    days_list = []
    start_date = start_time.date()
    end_date = end_time.date()
    delta = timedelta(days=1)

    while start_date <= end_date:
        days_list.append(start_date)
        start_date = start_date + delta
    return days_list


def get_best_temperature(MCP9808_temp_degc, BMP180_temp_degc, BMP280_temp_degc, HTU21D_temp_degc):

    # From Paul Kucera: For temperature use the MCP9808, but if that sensor is not reporting,
    # use the BMP, followed by the HTU

    if MCP9808_temp_degc is not None:
        temp_degc = MCP9808_temp_degc
    elif BMP180_temp_degc is not None:
        temp_degc = BMP180_temp_degc
    elif BMP280_temp_degc is not None:
        temp_degc = BMP280_temp_degc
    elif HTU21D_temp_degc is not None:
        temp_degc = HTU21D_temp_degc
    else:
        temp_degc = -9999

    return temp_degc


def get_station_name(MCP9808_station_name, BMP180_station_name, BMP280_station_name, HTU21D_station_name, rain_station_name, winddir_station_name, windspd_station_name):

    # Since we will not always have all of these files go through these until we find
    # one where the station name is set.

    if MCP9808_station_name is not None:
        name = MCP9808_station_name
    elif BMP180_station_name is not None:
        name = BMP180_station_name
    elif BMP280_station_name is not None:
        name = BMP280_station_name
    elif HTU21D_station_name is not None:
        name = HTU21D_station_name
    elif rain_station_name is not None:
        name = rain_station_name
    elif winddir_station_name is not None:
        name = winddir_station_name
    elif windspd_station_name is not None:
        name = windspd_station_name
    else:
        name = 'unknown'

    return name


def get_pressure(BMP180_pressure, BMP280_pressure):

    if BMP180_pressure is not None:
        if BMP180_pressure < 500:
            pressure = -9999
        else:
            pressure = BMP180_pressure
    elif BMP280_pressure is not None:
        if BMP280_pressure < 500:
            pressure = -9999
        else:
            pressure = BMP280_pressure
    else:
        pressure = -9999

    return pressure


# Checking the values for RH, wind speed, wind direction, and precip
def check_values(HTU21D_rh, windspd_windspd_ms, winddir_winddir_deg, rain_rain_mm):

    if HTU21D_rh is not None and HTU21D_rh > 0:
        rh = HTU21D_rh
        if rh > 100:
            rh = 100
    else:
        rh = -9999

    if windspd_windspd_ms is not None and windspd_windspd_ms >= 0:
        wspd = windspd_windspd_ms
    else:
        wspd = -9999

    if winddir_winddir_deg is not None and winddir_winddir_deg >= 0:
        wdir = winddir_winddir_deg
    else:
        wdir = -9999

    if rain_rain_mm is not None and rain_rain_mm >= 0:
        precip = rain_rain_mm
    else:
        precip = -9999

    return rh, wspd, wdir, precip


def compute_dewpoint(rh, temp_c):

    if rh is None or temp_c is None:
        return -9999

    if rh is -9999 or temp_c is -9999:
        return -9999

    if rh > 100.0:
        rh = 100.0
    elif rh < 0.001:
        rh = 0.001

    temp_k = temp_c + 273.15
    rhd = rh / 100.0
    log_rhd = -1.0 * math.log10(rhd)
    temp_dp_c = (temp_k / (0.000425 * temp_k * log_rhd + 1) ) - 273.15

    return temp_dp_c


# assumes stations are directories under the input_path
def get_stations_list(input_path):

    list = os.listdir(input_path)
    dir_list = []

    for entry in list:
        if os.path.isdir(os.path.join(input_path,entry)):
            dir_list.append(entry)

    return dir_list


def all_missing_values(temp_degc, rh, wspd, wdir, station_pressure, precip):

    if temp_degc == -9999 and rh == -9999 and wspd == -9999 and wdir == -9999 and station_pressure == -9999 and precip == -9999:
        return True
    else:
        return False


def main(arguments):

    parser = argparse.ArgumentParser(description=" Reading in 3D-Paws data and convert to an output file that can be ingested"
                                                 " into SPDB by the application SurfaceAscii2Spdb. This will output one minute"
                                                 " files over the start and end datetimes. The stations that are processed are found"
                                                 " by getting searching for files with the date in its name under the requested input_path. ",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_path', help = "A required with to data files.", type=str)
    parser.add_argument('output_path', help = "A required output path.", type=str)
    parser.add_argument('station_location_file', help = "A required station location file.", type=str)
    parser.add_argument('-max_lookback_time', help = "A lookback time in seconds. This is used when start_datatime is not set and a latest process time tmp file is not found", type=int )
    parser.add_argument('-start_datetime', help = "Date to start processing (YYYYMMDDHHMM). Leave blank to start at current time.", type=str )
    parser.add_argument('-end_datetime', help = "Date to end processing (YYYYMMDDHHMM). Leave blank if running on current time.", type=str )
    parser.add_argument('-write_ldata_info', help= "Option to write the latest_data_info file.", action="store_true")
    parser.add_argument('-tmp_file', help= "Optional tmp file location to store latest processed data time.", type=str )
    parser.add_argument('-debug', help= "Turn on debug messages", action="store_true")

    args = parser.parse_args(arguments)

    stations_list = get_stations_list(args.input_path)

    if args.tmp_file is not None:
        UseTmpFile = True
        tmp_filename = args.tmp_file
    else:
        UseTmpFile = False

    station_id = {}
    station_lat = {}
    station_lon = {}
    station_alt = {}

    for station in stations_list:
        id, lat,lon, alt = get_station_id_lat_lon_alt(args.station_location_file, station)
        station_id[station]  = id
        station_lat[station] = lat
        station_lon[station] = lon
        station_alt[station] = alt

    # start date time is not set assumes only processing latest time if available.
    # this will catch the case where the end_datetime is set but not a start_datetime
    if args.start_datetime is None:
        REALTIME_MODE = True
        print("WARN: -start_datetime not set, running on current time only.")
        current_time = datetime.utcnow()
        requested_end = current_time.strftime("%Y%m%d%H%M")
        if UseTmpFile and os.path.isfile(tmp_filename):
            tmpfile = open(tmp_filename, "r")
            line = tmpfile.readline()
            requested_start = line[0:12]
        else:
            new_dt_start = current_time - timedelta(seconds=args.max_lookback_time)
            requested_start = new_dt_start.strftime("%Y%m%d%H%M")

    elif args.start_datetime is not None and args.end_datetime is None:
        REALTIME_MODE = True
        print("WARN: -start_datetime set, -end_datetime not set. Will process all times between start_datetime and now.")
        current_time = datetime.utcnow()
        requested_start = args.start_datetime
        requested_end = current_time.strftime("%Y%m%d%H%M")
        if UseTmpFile and os.path.isfile(tmp_filename):
            tmpfile = open(tmp_filename, "r")
            line = tmpfile.readline()
            last_processed_time = line[0:12]
            rstart, lpt = get_start_and_end_datetime_objects(requested_start, last_processed_time)
            if lpt > rstart:
                print("ERROR: start_datetime is prior to the last processed time found")
                print("       in", tmp_filename,"Change start_datetime")
                print("       to be later or turn off using the tmp file.")
                print("start_datetime:    ", rstart.strtime("%Y%m%d%H%M"))
                print("Last process time: ", lpt.strtime("%Y%m%d%H%M"))
                sys.exit(-1)

    else:
        # if start and end times are giving don't look for tmp file.
        REALTIME_MODE = False
        requested_start = args.start_datetime
        requested_end = args.end_datetime

    print("INFO: start time ", requested_start[0:8], requested_start[8:12])
    print("INFO: end time   ", requested_end[0:8], requested_end[8:12], "\n")

    start_time, end_time = get_start_and_end_datetime_objects(requested_start, requested_end)
    process_time = start_time
    last_time = end_time

    days_in_interval = get_days_in_time_inteval(start_time, end_time)

    if args.debug:
      print("INFO: Days in time interval:")
      for day in days_in_interval:
        print("  ", day.strftime("%Y%m%d"))

    BMP180 = []
    BMP280 = []
    HTU21D = []
    MCP9808 = []
    rain = []
    winddir = []
    windspd = []

    number_of_files_found = 0
    min_dt = process_time
    max_dt = process_time

    for day in days_in_interval:

        # recursively search the input path for files with the this date in its name

        data_paths = glob(args.input_path + '/**/*_' + day.strftime("%Y%m%d") + '.dat', recursive=True)
        data_paths.sort()

        for path in data_paths:
            if os.path.isfile(path):
                number_of_files_found = number_of_files_found + 1

                if len(os.path.basename(path).split("_")) == 2:
                    instrument = os.path.basename(path).split("_")[0]
                    instrument = instrument.upper()
                else:
                    if os.path.basename(path).split("_")[1] == "direction":
                        instrument = "WINDDIR"
                    elif os.path.basename(path).split("_")[1] == "speed":
                        instrument = "WINDSPD"
                    elif os.path.basename(path).split("_")[1] == "tip":
                        instrument = "RAIN"

                station = path.replace(args.input_path, " ").split("/")[1]

                if args.debug:
                    print("INFO: Reading file", path)
                inFile = open(path, 'r')

                for indx, line in enumerate(inFile.readlines()):

                    parts = line.split()

                    try:
                        int(parts[0])
                    except ValueError:
                        if args.debug:
                            print("- WARN: Found garbage at start of line. Skipping this line:")
                            print(line)
                        continue

                    if len(parts) < 5:
                        continue

                    try:
                        dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    except ValueError:
                        if args.debug:
                            print("- WARN: bad value for datetime. Skipping this line:")
                            print(line)
                            continue

                    # These next few if statements are used to check if the time frame requesed can be narrowed
                    # based on the acutal data found within this time frame.
                    if number_of_files_found == 1 and indx == 0 and not REALTIME_MODE and dt >= start_time:
                        if args.debug:
                            print("INFO: First date found:", dt.strftime("%Y%m%d%H%M"))
                            print("      from file:", path)
                        # changing the starting process time to be the first time found.
                        process_time = dt
                        min_dt = dt
                        max_dt = dt

                    # If we find a time thats prior to the first time found then set process_time to that time.
                    # but don't go before the requested start time.
                    if dt < min_dt and not REALTIME_MODE and dt >= start_time:
                        if args.debug:
                            print("INFO: earlier time found:", dt.strftime("%Y%m%d%H%M"))
                            print("      from file", path)
                        process_time = dt
                        min_dt = dt

                    # find the last data time found and set last_time to it.
                    # don't go any later than the rquested end time.
                    if dt > max_dt and not REALTIME_MODE and dt <= end_time:
                        last_time = dt
                        max_dt = dt

                    if dt >= start_time and dt <= end_time:
                        if instrument == "BMP180":
                            BMP180.append(line.strip() + " " + station)
                        elif instrument == "BMP280":
                            BMP280.append(line.strip() + " " + station)
                        elif instrument == "HTU21D":
                            HTU21D.append(line.strip() + " " + station)
                        elif instrument == "MCP9808":
                            MCP9808.append(line.strip() + " " + station)
                        elif instrument == "RAIN":
                            rain.append(line.strip() + " " + station)
                        elif instrument == "WINDDIR":
                            winddir.append(line.strip() + " " + station)
                        elif instrument == "WINDSPD":
                            windspd.append(line.strip() + " " + station)

            else:
                if args.debug:
                    print("WARN: The following file does not exist -", path)

    if number_of_files_found == 0:
        print("\nWARN: No files found for the requested times...exiting.")
        sys.exit(0)

    '''
based on the application SurfaceAscii2Spdb:
// The input file should contain space-delimited ASCII.
// Alternatively you can specify the delimiter character.
// Comment lines start with '#'
// There should be one line for each station for each time
// If a value is unknown or missing, set to -9999
// From column 18 and up you can leave them out if not available.
//
// The input fields should be as follows
//      00 year
//      01 month
//      02 day
//      03 hour
//      04 min
//      05 sec
//      06 station-id - integer - set to -9999 if missing
//      07 station-name - string - set to 'unknown' if missing
//      08 latitude (deg)
//      09 longitude (deg)
//      10 height (m MSL)
//      11 temp (C)
//      12 dewpoint (C)
//      13 RH (%)
//      14 pressure (hPa)
//      15 windspeed (m/s)
//      16 winddirn (degT)
//      17 windgust (m/s)
//      18 precip_accum (mm)
//      19 precip_rate (mm/hr)
//      20 visibility (m)
//      21 rvr (m)
//      22 ceiling (m).
    '''

    obs_delta = timedelta(seconds=60)
    print()

    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    if not REALTIME_MODE:
        print("INFO: First data time found:", process_time.strftime("%Y%m%d%H%M"))
        print("INFO: Last data time found:",  last_time.strftime("%Y%m%d%H%M"))

    print("INFO: processing requested times.")

    while process_time <= last_time:

        print("- processing time:", process_time.strftime("%Y%m%d %H%M"))

        data_found = []

        for station in stations_list:

            # initialize the variables
            BMP180_temp_degc = None
            BMP180_station_name = None
            BMP180_station_pressure_hpa = None
            BMP180_sea_level_pressure_hpa = None
            BMP280_temp_degc = None
            BMP280_station_name = None
            BMP280_station_pressure_hpa = None
            BMP280_sea_level_pressure_hpa = None
            HTU21D_temp_degc = None
            HTU21D_rh = None
            HTU21D_station_name = None
            MCP9808_temp_degc = None
            MCP9808_station_name = None
            rain_rain_mm = None
            rain_station_name = None
            winddir_winddir_deg = None
            winddir_station_name = None
            windspd_windspd_ms = None
            windspd_station_name = None

            if len(BMP180) > 0:
                BMP180.sort()
                for indx, entry in enumerate(BMP180):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        BMP180_temp_degc = float(parts[5])
                        BMP180_station_name = parts[-1]
                        BMP180_station_pressure_hpa = float(parts[7])
                        BMP180_sea_level_pressure_hpa = float(parts[8])
                        BMP180.pop(indx)
                    elif dt < process_time:
                        BMP180.pop(indx)
                    elif dt > process_time:
                        break

            if len(BMP280) > 0:
                BMP280.sort()
                for indx, entry in enumerate(BMP280):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        BMP280_temp_degc = float(parts[5])
                        BMP280_station_name = parts[-1]
                        BMP280_station_pressure_hpa = float(parts[7])
                        BMP280_sea_level_pressure_hpa = float(parts[8])
                        BMP280.pop(indx)
                    elif dt < process_time:
                        BMP280.pop(indx)
                    elif dt > process_time:
                        break

            if len(HTU21D) > 0:
                HTU21D.sort()
                for indx, entry in enumerate(HTU21D):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        HTU21D_temp_degc = float(parts[5])
                        HTU21D_rh = float(parts[7])
                        HTU21D_station_name = parts[-1]
                        HTU21D.pop(indx)
                    elif dt < process_time:
                        HTU21D.pop(indx)
                    elif dt > process_time:
                        break

            if len(MCP9808) > 0:
                MCP9808.sort()
                for indx, entry in enumerate(MCP9808):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        MCP9808_temp_degc = float(parts[5])
                        MCP9808_station_name = parts[-1]
                        MCP9808.pop(indx)
                    elif dt < process_time:
                        MCP9808.pop(indx)
                    elif dt > process_time:
                        break

            if len(rain) > 0:
                # From Paul Kucera: rain is a 15 minute accumulation
                rain.sort()
                for indx, entry in enumerate(rain):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        if len(parts) == 8:
                            rain_rain_mm = float(parts[6])
                        else: # WMO data does not include seconds
                            rain_rain_mm = float(parts[5])
                        rain_station_name = parts[-1]
                        rain.pop(indx)
                    elif dt < process_time:
                        rain.pop(indx)
                    elif dt > process_time:
                        break

            if len(winddir) > 0:
                winddir.sort()
                for indx, entry in enumerate(winddir):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        winddir_winddir_deg = float(parts[7])
                        winddir_station_name = parts[-1]
                        winddir.pop(indx)
                    elif dt < process_time:
                        winddir.pop(indx)
                    elif dt > process_time:
                        break

            if len(windspd) > 0:
                windspd.sort()
                for indx, entry in enumerate(windspd):
                    parts = entry.split()
                    dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]), int(parts[3]), int(parts[4]), 0)
                    st = parts[-1]
                    if dt == process_time and st == station:
                        if len(parts) == 8:
                            windspd_windspd_ms = float(parts[6])
                        else: # WMO data does not include seconds
                            windspd_windspd_ms = float(parts[5])
                        windspd_station_name = parts[-1]
                        windspd.pop(indx)
                    elif dt < process_time:
                        windspd.pop(indx)
                    elif dt > process_time:
                        break

            temp_degc = get_best_temperature(MCP9808_temp_degc, BMP180_temp_degc, BMP280_temp_degc, HTU21D_temp_degc)
            temp_dp_degc = compute_dewpoint(HTU21D_rh, HTU21D_temp_degc)
            station_name = get_station_name(MCP9808_station_name, BMP180_station_name, BMP280_station_name, HTU21D_station_name, rain_station_name,
                                            winddir_station_name, windspd_station_name)
#            id, lat, lon, alt = get_station_id_lat_lon_alt(args.station_location_file, station_name)

            rh, wspd, wdir, precip = check_values(HTU21D_rh, windspd_windspd_ms, winddir_winddir_deg, rain_rain_mm)


            station_pressure = get_pressure(BMP180_station_pressure_hpa, BMP280_station_pressure_hpa)
            sea_level_pressure = get_pressure(BMP180_sea_level_pressure_hpa, BMP280_sea_level_pressure_hpa)


            # precip is 15 min accumulation. Multiply by 4 to get rate of mm/hr
            if precip >= 0:
                precip_rate = precip * 4.0
            else:
                precip_rate = -9999

            # check if all values are missing data valiues. If so no need to write this time
            if not all_missing_values(temp_degc, rh, wspd, wdir, sea_level_pressure, precip):
                data_list = [process_time, station_id[station_name], station_lat[station_name], station_lon[station_name],
                             station_alt[station_name], temp_degc, temp_dp_degc, rh, sea_level_pressure, wspd, wdir, precip, precip_rate ]
                data_found.append(data_list)


        if len(data_found) > 0:
            outFileName = process_time.strftime("%Y%m%d_%H%M_3dPaws.ascii")
            output_path = os.path.join(args.output_path, process_time.strftime("%Y%m%d"))
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_full_path = os.path.join(output_path, outFileName)
            outputFile = open(output_full_path, 'w')
            outputFile.write("# year month day hour min sec station_id station_name latitude Longitude height(m) temp(c) dpt(c) rh(%) sea_level_pres(hPa) wind_spd(m/s) wind_dir(deg) wind)gust(m/s) precip(15min mm) precip_rate(mm/hr)\n")

            for data in data_found:
                outputFile.write(data[0].strftime("%Y %m %d %H %M 00 -9999.0 "))
                outputFile.write("%s %10.5f %10.5f %7.1f %8.2f %8.2f %7.1f %8.2f %8.2f %8.2f -9999.0 %8.2f %8.2f\n"
                                 % (data[1], data[2], data[3], data[4],
                                    data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12]))

            outputFile.close()
            print("  - Wrote file:", output_full_path)

            if args.write_ldata_info:
                subprocess.call(["LdataWriter", "-rpath", process_time.strftime("%Y%m%d") + "/" + outFileName, "-dir", args.output_path, "ext ascii"])
                time.sleep(2)

            if UseTmpFile:
                tmpfile = open(tmp_filename, "w")
                tmpfile.write(process_time.strftime("%Y%m%d%H%M"))
                tmpfile.close()

        process_time = process_time + obs_delta

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
