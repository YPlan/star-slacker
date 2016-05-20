# Put the slack channel you want to post to
slack_channel = '#slack-channel-here'

# This file is generated in the Admin Console and contains info for Google OAuth
google_credentials = 'google-auth.json'

# Your apps (package names) here
apps = ["com.example.app", "com.example.anotherapp"]

# How many days back do you want to look for reviews (default is 2)
# Should be >=2 because of the delay it takes to fill data in your GCS bucket
days_in_past = 2