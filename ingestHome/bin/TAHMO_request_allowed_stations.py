#!/usr/bin/env python

import urllib, urllib2, base64, json, csv

# Fill in your API credentials
API_ID 				= '1HECW9JETU86A2O27SF7X48LO'
API_SECRET 			= '7yCW2nz3sIWctxE4J9MBSzB4A3g/LE6Sulelcd3o8YD'

# Generate base64 encoded authorization string
basicAuthString 	= base64.encodestring('%s:%s' % (API_ID, API_SECRET)).replace('\n', '')

# Function to request data from API
def apiRequest (url, params = {}):

	# Encode optional parameters
	encodedParams 		= urllib.urlencode(params)

	# Set API endpoint
	request 			= urllib2.Request(url + '?' + encodedParams)

	# Add authorization header to the request
	request.add_header("Authorization", "Basic %s" % basicAuthString)	

	try:
		response 		= urllib2.urlopen(request)
		return response.read()
	except urllib2.HTTPError, err:
		if err.code == 401:
			print "Error: Invalid API credentials";
			quit()
		elif err.code == 404:
			print "Error: The API endpoint is currently unavailable";
			quit()
		else:
			print err
			quit()

# Request stations from API
response 				= apiRequest("https://tahmoapi.mybluemix.net/v1/stations")
decodedResponse			= json.loads(response)

# Check if API responded with an error
if(decodedResponse['status'] == 'error'):
	print "Error:", decodedResponse['error']

# Check if API responded with success
elif(decodedResponse['status'] == 'success'):

	# Print the amount of stations that were retrieved in this API call
	print "API call success:", len(decodedResponse['stations']), "stations retrieved"

	# Generate CSV file to export data
	with open('stations.csv', 'wb') as csvFile:

		# Create csv writer object
		writer 			= csv.writer(csvFile)

		# Loop through received stations
		for station in decodedResponse['stations']:

			# Set default values for station properties
			station.setdefault('id', '')
			station.setdefault('name', '')
			station.setdefault('countryCode', '')
			station.setdefault('location', {'lng': '', 'lat': ''})
			station.setdefault('lastMeasurement', '')

			# Write a row to the CSV file containing station id, countryCode, station name, longitude, latitude and lastMeasurement
			# Note: Special characters are removed from name property
			writer.writerow([station['id']] + [station['countryCode']] + [station['name'].encode('ascii', 'ignore')] + [station['location']['lng']] + [station['location']['lat']] + [station['lastMeasurement']])
