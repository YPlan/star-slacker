#!/usr/bin/env python
# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import csv
from datetime import datetime, timedelta
from io import BytesIO

import dateutil.parser
from googleapiclient import discovery, http
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from slacker import Slacker

import settings
import secrets


def lambda_handler(event, context):
    slack = Slacker(secrets.slack_token)

    for app in settings.apps:
        app_filename = construct_filename(app)
        file_buf = BytesIO()
        download_report(secrets.google_bucket, app_filename, file_buf)
        file_buf.seek(0)
        process_reviews(file_buf, slack)


def construct_filename(app_package):
    format_string = 'reviews_{0}_{1}{2}.csv'
    current_date = datetime.utcnow()
    return format_string.format(app_package, current_date.year, '%02d' % current_date.month)


def download_report(bucket, filename, out_file):
    service = create_service()

    # Use get_media instead of get to get the actual contents of the object.
    # http://g.co/dev/resources/api-libraries/documentation/storage/v1/python/latest/storage_v1.objects.html#get_media
    full_path_filename = 'reviews/' + filename
    req = service.objects().get_media(bucket=bucket, object=full_path_filename)

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


def create_service():
    # Get the application default credentials. When running locally, these are
    # available after running `gcloud init`. When running on compute
    # engine, these are available from the environment.

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        settings.google_credentials,
        scopes='https://www.googleapis.com/auth/devstorage.read_only'
    )
    # Construct the service object for interacting with the Cloud Storage API -
    # the 'storage' service, at version 'v1'.
    # You can browse other available api services and versions here:
    #     http://g.co/dev/api-client-library/python/apis/
    return discovery.build('storage', 'v1', credentials=credentials)


def process_reviews(file_buf, slack):
    decoded_csv_file = file_buf.read().decode('utf-16').encode('utf-8')
    csv_reader = csv.reader(BytesIO(decoded_csv_file), delimiter=b',')
    next(csv_reader, None)  # skip the headers

    for row in csv_reader:
        submitted_at = row[7]
        # only show reviews from the last N hours
        if (datetime.utcnow() - dateutil.parser.parse(submitted_at, ignoretz='true')) > timedelta(settings.days_in_past):
            continue

        app_name = row[0]
        version = row[2]
        device = row[4]
        rating = row[9]
        title = row[10]
        text = row[11]
        url = row[15]
        msg = format_message(title, text, submitted_at, rating, device, version, url, app_name)

        slack.chat.post_message(settings.slack_channel, msg)


def format_message(title, text, submitted_at, rating, device, version, url, app_name):
    stars = ''

    for i in range(0, int(rating)):
        stars += '★'

    for i in range(0, 5 - int(rating)):
        stars += '☆'

    if not url:  # it's just a rating only format the fields we need
        format_rating = 'Application: {4}\nRating: {0}\nSubmitted at: {1}\nDevice: {2}\nVersion: {3}\n'
        return format_rating.format(stars, submitted_at, device, version, app_name)
    # full review format
    format_review = 'Application: {7}\nRating: {3}\nText: {0} {1}\nSubmitted at: {2}\nDevice: {4}\nVersion: {5}\nURL: {6}'

    return format_review.format(title, text, submitted_at, stars, device, version, url, app_name)


if __name__ == '__main__':
    lambda_handler("", "")
