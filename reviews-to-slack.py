#!/usr/bin/env python
# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from io import BytesIO
from slacker import Slacker
from datetime import datetime, timedelta

from googleapiclient import discovery
from googleapiclient import http
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

import dateutil.parser
import csv

slackToken = 'slack-token-here'
slackChannel = '#slack-channel-here'

# You get this from the Reviews page in the Google Play Console
googleBucket = 'pubsite_prod_rev_your-bucket-here'

# This is generated in the Admin Console and contains info for Google OAuth
json_file = 'google-auth.json'

# Our apps
apps = ["com.yplanapp", "co.cinemaclub", "com.yplanapp.access"]
daysInPast = 1

slack = Slacker(slackToken)


def formatMessage(title, text, submitted_at, rating, device, version, url, appName):
    stars = ''

    for i in range(0, int(rating)):
        stars += '★'

    for i in range(0, 5 - int(rating)):
        stars += '☆'

    if not url:  # it's just a rating only format the fields we need
        formatRating = 'Application: {4}\nRating: {0}\nSubmitted at: {1}\nDevice: {2}\nVersion: {3}\n'
        return formatRating.format(stars, submitted_at, device, version, appName)
    # full review format
    formatReview = 'Application: {7}\nRating: {3}\nText: {0} {1}\nSubmitted at: {2}\nDevice: {4}\nVersion: {5}\nURL: {6}'

    return formatReview.format(title, text, submitted_at, stars, device, version, url, appName)


def processReviewsFile(filename):
    with open(filename, 'r') as csvfile:
        decodedCsvFile = csvfile.read().decode('utf-16').encode('utf-8')
        csvReader = csv.reader(BytesIO(decodedCsvFile), delimiter=b',')
        next(csvReader, None)  # skip the headers
        for row in csvReader:
            submitted_at = row[7]
            # only show reviews from the last 24hrs
            if (datetime.utcnow() - dateutil.parser.parse(submitted_at, ignoretz='true')) > timedelta(daysInPast):
                continue
            text = row[11]
            title = row[10]
            appName = row[0]
            rating = row[9]
            device = row[4]
            url = row[15]
            version = row[2]
            msg = formatMessage(title, text, submitted_at, rating, device, version, url, appName)
            slack.chat.post_message(slackChannel, msg)


def constructFilename(appPackage):
    formatString = 'reviews_{0}_{1}{2}.csv'
    currentDate = datetime.utcnow()
    return formatString.format(appPackage, currentDate.year, '%02d' % currentDate.month)


def create_service():
    # Get the application default credentials. When running locally, these are
    # available after running `gcloud init`. When running on compute
    # engine, these are available from the environment.

    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes='https://www.googleapis.com/auth/devstorage.read_only')
    # Construct the service object for interacting with the Cloud Storage API -
    # the 'storage' service, at version 'v1'.
    # You can browse other available api services and versions here:
    #     http://g.co/dev/api-client-library/python/apis/
    return discovery.build('storage', 'v1', credentials=credentials)


def downloadReport(bucket, filename, out_file):
    service = create_service()

    # Use get_media instead of get to get the actual contents of the object.
    # http://g.co/dev/resources/api-libraries/documentation/storage/v1/python/latest/storage_v1.objects.html#get_media
    fullPathFilename = 'reviews/' + filename
    req = service.objects().get_media(bucket=bucket, object=fullPathFilename)

    downloader = http.MediaIoBaseDownload(out_file, req)

    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except HttpError as e:
            print("Failed to download ", e)
            return
        print("Download {}%.".format(int(status.progress() * 100)))

    return out_file


def main():
    for app in apps:
        appFilename = constructFilename(app)
        downloadReport(googleBucket, appFilename, open(appFilename, 'w'))
        processReviewsFile(appFilename)

if __name__ == '__main__':
    main()
