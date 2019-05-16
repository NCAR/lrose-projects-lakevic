#!/usr/bin/env python

import argparse
import sys
import json
from datetime import datetime
from datetime import timedelta
import urllib
import urllib2
import base64
import os
import subprocess
import math
from time import sleep
import string

# Fill in your API credentials
API_ID = '1HECW9JETU86A2O27SF7X48LO'
API_SECRET = '7yCW2nz3sIWctxE4J9MBSzB4A3g/LE6Sulelcd3o8YD'

# Generate base64 encoded authorization string
basicAuthString = base64.encodestring('%s:%s' % (API_ID, API_SECRET)).replace('\n', '')

# Function to request data from API
def apiRequest (url, params = {}):

    # Encode optional parameters
    encodedParams = urllib.urlencode(params)

    # Set API endpoint
    request = urllib2.Request(url + '?' + encodedParams)

    # Add authorization header to the request
    request.add_header("Authorization", "Basic %s" % basicAuthString)

    try:
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.HTTPError as err:
        if err.code == 401:
            print("Error: Invalid API credentials")
            quit()
        elif err.code == 404:
            print("Error: The API endpoint is currently unavailable")
            quit()
        else:
            print(err)
            quit()


def get_json_data():
    # Request stations from API

    # TODO: change back to https (not working on MAC)
    response = apiRequest("https://tahmoapi.mybluemix.net/v1/stations")
    decodedResponse	= json.loads(response)

    # Check if API responded with an error
    if(decodedResponse['status'] == 'error'):
        print("Error:", decodedResponse['error'])

    # Check if API responded with success
    elif(decodedResponse['status'] == 'success'):

        # Print the amount of stations that were retrieved in this API call
        print("API call success:", len(decodedResponse['stations']), "stations retrieved")
        return decodedResponse


def get_timeseries_data(station, startDate, endDate):

    lastMeasurement = startDate

    # Set default values for station properties
    station.setdefault('id', 'unkown')
    station.setdefault('name', 'unkown')
    station.setdefault('lastMeasurement', '')

    print "Start receiving timeseries for station", station['id']


    # Maximum attempts as a security measure for the while loop
    attempt = 0;

    # The timeseries call currently only returns 4 weeks of data, therefore a while loop is used until
    # the last data is retrieved (maximum attempts accounts for 2 years of data)
    while ((lastMeasurement < station['lastMeasurement'][0:13] and lastMeasurement < endDate) and attempt < (2 * 4 * 13)):

        attempt += 1;

        # Request timeseries for specific station
        # TODO: change back to https
        tsResponse = apiRequest("https://tahmoapi.mybluemix.net/v1/timeseries/" + station['id'] + "/",
                                {'startDate': lastMeasurement, 'endDate': endDate})
        decodedTsResponse = json.loads(tsResponse)

        # Check if API responded with an error
        if (decodedTsResponse['status'] == 'error'):
            print "Error:", decodedTsResponse['error']


        # Check if API responded with success
        elif (decodedTsResponse['status'] == 'success'):

            # Print success message
            print "API call success: timeseries for ", station['id'], "startdate ", lastMeasurement

            return decodedTsResponse

def get_data_value(data, process_time):

    value = -9999
    if len(data) > 0:
        for indx, entry in enumerate(data):
            dt = entry[0]
            if dt == process_time:
                value = entry[1]
                data.pop(indx)
            elif dt < process_time:
                data.pop(indx)
            elif dt > process_time:
                break

    return float(value)


def all_missing_values(temp_degc, rh, wspd, wdir, wgust, pressure, precip):

    if temp_degc == -9999 and rh == -9999 and wspd == -9999 and wdir == -9999 and wgust and pressure == -9999 and precip == -9999:
        return True
    else:
        return False


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

def write_the_data(obs_delta, station_name, station_lat, station_lon, station_elev, args_output_path, write_ldatainfo,
                   pressure_data, temperature_data, rh_data, winddir_data, windspd_data, windgust_data, precip_data):

    # find the start and end times. It is possible each of these arrays could have a different start and end
    # time so find the min and max times from all of these.
    end_time = datetime(1900, 1, 1, 0, 0, 0)
    start_time = datetime.utcnow()
    print
    for data in [pressure_data, temperature_data, rh_data, precip_data, winddir_data, windspd_data, windgust_data]:
        for info in data:
            if info[0] > end_time:
                end_time = info[0]
            if info[0] < start_time:
                start_time = info[0]

    print "start_time = ", start_time.strftime("%Y%m%d %H%M")
    print "end_time = ", end_time.strftime("%Y%m%d %H%M")

    pressure_data.sort()
    temperature_data.sort()
    rh_data.sort()
    winddir_data.sort()
    windspd_data.sort()
    windgust_data.sort()
    precip_data.sort()

    process_time = start_time

    while process_time <= end_time:

        #
        # TODO: Check if this is station pressure or sea level pressure
        #
        sea_level_pressure_hpa = get_data_value(pressure_data, process_time)
        if not sea_level_pressure_hpa == -9999:
            sea_level_pressure_hpa = sea_level_pressure_hpa * 10

        temp_degc = get_data_value(temperature_data, process_time)
        RH = get_data_value(rh_data, process_time)
        if not RH == -9999.0:
            RH = RH * 100
        temp_dp_degc = compute_dewpoint(RH, temp_degc)
        #
        # TODO: Need to check precip. I think it is 5 minute acccumulations if that is the report freqency of the station
        #
        precip = get_data_value(precip_data, process_time)
        if not precip == -9999:
            precip_rate = precip * 12
        else:
            precip_rate = -9999

        wdir = get_data_value(winddir_data, process_time)
        wspd = get_data_value(windspd_data, process_time)
        wgust = get_data_value(windgust_data, process_time)

        data_list = []
        # check if all values are missing data valiues. If so no need to write this time
        if not all_missing_values(temp_degc, RH, wspd, wdir, wgust, sea_level_pressure_hpa, precip):
            data_list = [process_time, station_name, float(station_lat), float(station_lon),
                         float(station_elev), temp_degc, temp_dp_degc, RH, sea_level_pressure_hpa, wspd, wdir, wgust,
                         precip, precip_rate]

        if len(data_list) > 0:
            outFileName = process_time.strftime("%Y%m%d_%H%M_TAHMO.ascii")
            output_path = os.path.join(args_output_path, process_time.strftime("%Y%m%d"))
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_full_path = os.path.join(output_path, outFileName)
            outputFile = open(output_full_path, 'w')
            outputFile.write(
                "# year month day hour min sec station_id station_name latitude Longitude height(m) temp(c) dpt(c) rh(%) sea_level_pres(hPa) wind_spd(m/s) wind_dir(deg) wind)gust(m/s) precip(5min mm) precip_rate(mm/hr)\n")

            outputFile.write(data_list[0].strftime("%Y %m %d %H %M 00 -9999.0 "))
            outputFile.write("%s %10.5f %10.5f %7.1f %8.2f %8.2f %7.1f %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f\n"
                             % (data_list[1], data_list[2], data_list[3], data_list[4], data_list[5], data_list[6],
                                data_list[7], data_list[8], data_list[9], data_list[10], data_list[11], data_list[12],
                                data_list[13]))

            outputFile.close()
            print "  - Wrote file:", output_full_path

            if write_ldatainfo:
                subprocess.call(["LdataWriter", "-rpath", process_time.strftime("%Y%m%d") + "/" + outFileName, "-dir",
                                 args_output_path, "ext ascii"])
                sleep(2)

        process_time = process_time + obs_delta

def write_requested_data(args_output_path, write_ldatainfo, obs_delta, output_data, station_report_interval):

    # find the start and end times. It is possible each of these arrays could have a different start and end
    # time so find the min and max times from all of these.
    end_time = datetime(1970, 1, 1, 0, 0, 0)
    start_time = datetime.utcnow()
    print
    for data in output_data:
        if data[0] > end_time:
            end_time = data[0]
        if data[0] < start_time:
            start_time = data[0]

    process_time = start_time

    while process_time <= end_time:

        outFileName = process_time.strftime("%Y%m%d_%H%M_TAHMO.ascii")
        output_path = os.path.join(args_output_path, process_time.strftime("%Y%m%d"))
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_full_path = os.path.join(output_path, outFileName)

        if output_data[0][0] == process_time:
            outputFile = open(output_full_path, 'w')
            outputFile.write(
                "# year month day hour min sec station_id station_name latitude Longitude height(m) temp(c) dpt(c) rh(%) station_pres(hPa) wind_spd(m/s) wind_dir(deg) wind_gust(m/s) precip(5min mm) precip_rate(mm/hr)\n")

        while len(output_data) > 0:

            if output_data[0][0] == process_time:
                #
                # use station interval (minutes) information to estimate hourly precip rate
                #
                rate_multiplier = 0
                for st, interval in station_report_interval:
                    if st == output_data[0][1]:
                        rate_multiplier = int(60 / interval)
                precip_accum = float(output_data[0][12])
                rate = precip_accum * rate_multiplier

                outputFile.write(output_data[0][0].strftime("%Y %m %d %H %M 00 -9999.0 "))
                outputFile.write("%s %10.5f %10.5f %7.1f %8.2f %8.2f %7.1f %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f\n"
                                 % (output_data[0][1], output_data[0][2], output_data[0][3], output_data[0][4], output_data[0][5], output_data[0][6],
                                    output_data[0][7], output_data[0][8], output_data[0][9], output_data[0][10], output_data[0][11], output_data[0][12],
                                    rate) )
                output_data.pop(0)
            else:
                break

        outputFile.close()
        print "  - Wrote file:", output_full_path

        if write_ldatainfo:
            subprocess.call(["LdataWriter", "-rpath", process_time.strftime("%Y%m%d") + "/" + outFileName, "-dir",
                                args_output_path, "ext ascii"])
            sleep(2)

        process_time = process_time + obs_delta


def main(arguments):

    parser = argparse.ArgumentParser(description=
                                     "Takes in either a json formated TAHMO data file requests the data "
                                     "from the TAHMO http server. If -input_file is set then this script "
                                     "assumes a data file will be processed. If -input_file is not set "
                                     "then the script assumes a data request to the TAHMO and expects the "
                                     "-start_date and -end_date are set. The output are space deleneated "
                                     "ascii files which can be read by SurfaceAscii2Spdb.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output_path', help = "A required output path.", type=str)
    parser.add_argument('-input_file', help = "An optional json data file.", type=str)
    parser.add_argument('-start_time', help = "An optional start date in the format YYYY=MM-DDTHH:MM.", type=str)
    parser.add_argument('-end_time',   help = "An optional end date in the format YYYY=MM-DDTHH:MM.", type=str)
    parser.add_argument('-write_ldata_info', help= "Option to write the latest_data_info file.", action="store_true")
    parser.add_argument('-debug', help= "Turn on debug messages", action="store_true")

    args = parser.parse_args(arguments)

    if args.input_file is None:
        if args.start_time is None or args.end_time is None:
            print
            print "ERROR: You must set either the input_file or start_time and end_time."
            print "       input_files =", args.input_file
            print "       start_time =", args.start_time
            print "       end_time =", args.end_time
            sys.exit(1)
        else:
            if args.debug:
                print
                print "INFO: Setting to data request mode."
                print "     startDate:", args.start_time
                print "     endDate:  ", args.end_time
            request_data = True
    else:
        if args.debug:
            print "INFO: Setting to file input mode."
        request_data = False

    obs_delta = timedelta(minutes=5)

    if (request_data):

        #
        # These are used in the data request to the TAHMO http server
        #
        startDate = args.start_time
        endDate = args.end_time

        #
        # used to store all the requested data
        #
        output_data = []

        #
        # Request the allowed stations
        #
        stationRequest = get_json_data()

        station_report_interval = []

        for station in stationRequest['stations']:

            station_id = station['id']
            station_location = station['location']
            station_elev = station['elevation']
            station_variables = station['variables']
            time_zone_offset = station['timezoneOffset']
            time_zone = station['timezone']

            station_lon = station_location['lng']
            station_lat = station_location['lat']

            #
            # Assinging the last for digits of the station id to station_name
            # this is used
            #
            station_name = station_id[-4:]

            # print out the station information
            if args.debug:
                print "Station Information:\n"
                print "station_id:", station_id
                print "station_latitude:", station_lat
                print "station_longitude:", station_lon
                print "station_elevation:", station_elev
                print "Time Zone:", time_zone
                print "Time Zone offset:", time_zone_offset
                print

            station_variables.sort()
            if args.debug:
                print "Available variables:\n"
                for variable in station_variables:
                    print variable
                print

            pressure_data = []
            temperature_data = []
            rh_data = []
            winddir_data = []
            windspd_data = []
            windgust_data = []
            precip_data = []

            station_data = get_timeseries_data(station, startDate, endDate)

            if station_data is None:
                print "ERROR: Unable to retrieve timeseries data from", station_id
                print
                continue

            for variable in station_data['station']['variables']:

                if args.debug:
                    print "Processing varaible:", variable

                try:
                    for time, value in sorted(station_data['timeseries'][variable].items()):

                        if variable == "atmosphericpressure":
                            pressure_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            pressure_data.append( (pressure_time, value, station_name, station_lat, station_lon, station_elev) )

                        elif variable == "precipitation":
                            precip_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            precip_data.append( (precip_time, value, station_name, station_lat, station_lon, station_elev ) )

                        elif variable == "relativehumidity":
                            rh_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            rh_data.append( (rh_time, value, station_name, station_lat, station_lon, station_elev) )

                        elif variable == "temperature":
                            temperature_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            temperature_data.append( (temperature_time, value, station_name, station_lat, station_lon, station_elev) )

                        elif variable == "winddirection":
                            winddir_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            winddir_data.append( (winddir_time, value, station_name, station_lat, station_lon, station_elev) )

                        elif variable == "windspeed":
                            windspd_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            windspd_data.append( (windspd_time, value, station_name, station_lat, station_lon, station_elev) )

                        elif variable == "windgusts":
                            windgust_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
                            windgust_data.append( (windgust_time, value, station_name, station_lat, station_lon, station_elev) )

                except:
                    print "ERROR: Unable to process variable", variable


            if len(pressure_data) + len(temperature_data) + len(rh_data) + len(precip_data) + len(winddir_data) + len(windspd_data) + len(windgust_data)  == 0:
                print "ERROR: No data found for station", station_id
                print
                continue

            # find the start and end times. It is possible each of these arrays could have a different start and end
            # time so find the min and max times from all of these.
            end_time = datetime(1900, 1, 1, 0, 0, 0)
            start_time = datetime.utcnow()
            for data in [pressure_data, temperature_data, rh_data, precip_data, winddir_data, windspd_data,
                         windgust_data]:
                for info in data:
                    if info[0] > end_time:
                        end_time = info[0]
                    if info[0] < start_time:
                        start_time = info[0]

            if end_time - start_time >= timedelta(days=1):
                line_split = str( (end_time - start_time)).split()
                number_of_days = int(line_split[0])
                time_split = line_split[2].split(":")
                hours = int(time_split[0]) + number_of_days * 24
                minutes = int(time_split[1])
            else:
                time_split = str( (end_time - start_time)).split(":")
                hours = int(time_split[0])
                minutes = int(time_split[1])


            minutes_interval = hours * 60 + minutes
            times_processed = 0

            pressure_data.sort()
            temperature_data.sort()
            rh_data.sort()
            winddir_data.sort()
            windspd_data.sort()
            windgust_data.sort()
            precip_data.sort()
            process_time = start_time

            while process_time <= end_time:

                #
                # TODO: Check if this is station pressure or sea level pressure
                #
                if len(pressure_data) > 0:
                    sea_level_pressure_hpa = get_data_value(pressure_data, process_time)
                    if not sea_level_pressure_hpa == -9999:
                        sea_level_pressure_hpa = sea_level_pressure_hpa * 10
                else:
                    sea_level_pressure_hpa = -9999

                if len(temperature_data) > 0:
                    temp_degc = get_data_value(temperature_data, process_time)
                else:
                    temp_degc = -9999

                if len(rh_data) > 0:
                    RH = get_data_value(rh_data, process_time)
                    if not RH == -9999.0:
                        RH = RH * 100
                else:
                    RH = -9999

                temp_dp_degc = compute_dewpoint(RH, temp_degc)

                #
                # TODO: Need to check precip. I think it is 5 minute acccumulations if that is the report freqency of the station
                #

                if len(precip_data) > 0:
                    precip = get_data_value(precip_data, process_time)
                    if not precip == -9999:
                       precip_rate = precip * 12
                    else:
                        precip_rate = -9999
                else:
                    precip = -9999
                    precip_rate = -9999

                if len(winddir_data) > 0:
                    wdir = get_data_value(winddir_data, process_time)
                else:
                    wdir = -9999

                if len(windspd_data) > 0:
                    wspd = get_data_value(windspd_data, process_time)
                else:
                    wspd = -9999

                if len(windgust_data) > 0:
                    wgust = get_data_value(windgust_data, process_time)
                else:
                    wgust = -9999

                # check if all values are missing data valiues. If so no need to write this time
                if not all_missing_values(temp_degc, RH, wspd, wdir, wgust, sea_level_pressure_hpa, precip):
                    output_data.append([process_time, station_name, float(station_lat), float(station_lon),
                                 float(station_elev), temp_degc, temp_dp_degc, RH, sea_level_pressure_hpa, wspd, wdir,
                                 wgust, precip, precip_rate])
                    times_processed = times_processed + 1

                process_time = process_time + obs_delta

            data_interval = round( float(minutes_interval) / float(times_processed))
            if data_interval > 0 and data_interval <= 5:
                data_interval = 5
            if data_interval > 5 and data_interval <= 10:
                data_interval = 10
            if data_interval > 10 and data_interval <= 15:
                data_interval = 15

            station_report_interval.append( (station_name, data_interval))

            print "minutes_interval:",minutes_interval, "times_processed:", times_processed
            print "Station:", station_name, "DataInterval:", data_interval
            print

        output_data.sort()
        write_requested_data(args.output_path, args.write_ldata_info, obs_delta, output_data, station_report_interval)

    else:

        print "INFO: Processing file", args.input_file

        file = open(args.input_file, 'r')

        # Load the json data
        jason_data = json.load(file)

        # pulling out station information
        station_list = jason_data['station']

        station_id = station_list['id']
        station_location = station_list['location']
        station_elev = station_list['elevation']
        station_variables = station_list['variables']
        time_zone_offset = station_list['timezoneOffset']
        time_zone = station_list['timezone']

        station_lon = station_location['lng']
        station_lat = station_location['lat']

        station_name = station_id[-4:]

        # print out the station information
        if args.debug:
            print("Station Information:\n")
            print("station_id:", station_id)
            print("station_latitude", station_lat)
            print("station_longitude:", station_lon)
            print("station_elevation:", station_elev)
            print("Time Zone:", time_zone)
            print("Time Zone offset:", time_zone_offset)
            print()

            station_variables.sort()
            print("Available variables:\n")
            for variable in station_variables:
                print(variable)
            print()

        pressure_data = []
        temperature_data = []
        rh_data = []
        winddir_data = []
        windspd_data = []
        windgust_data = []
        precip_data = []

        # pull out the time series data
        station_data = jason_data['timeseries']

        pressure = station_data['atmosphericpressure']
        for time, value in pressure.items():
            pressure_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            pressure_data.append( (pressure_time, value) )

        precip = station_data['precipitation']
        for time, value in precip.items():
            precip_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            precip_data.append( (precip_time, value) )

        rh = station_data['relativehumidity']
        for time, value in rh.items():
            rh_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            rh_data.append( (rh_time, value) )

        temperature = station_data['temperature']
        for time, value in temperature.items():
            temperature_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            temperature_data.append( (temperature_time, value) )

        winddir = station_data['winddirection']
        for time, value in winddir.items():
            winddir_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            winddir_data.append( (winddir_time, value) )

        windspd = station_data['windspeed']
        for time, value in windspd.items():
            windspd_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            windspd_data.append( (windspd_time, value) )

        windgust = station_data['windgusts']
        for time, value in windgust.items():
            windgust_time = datetime(int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
            windgust_data.append( (windgust_time, value) )

        write_the_data(obs_delta, station_name, station_lat, station_lon, station_elev, args.output_path, args.write_ldata_info,
                       pressure_data, temperature_data, rh_data, winddir_data, windspd_data, windgust_data, precip_data)

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

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
