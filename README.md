# Introduction

Star Slacker is a simple util for fetching user reviews from the Play Store and posting these to a Slack channel

# Pre-requisites

* Google access
  * Google automatically creates a Google Cloud Storage bucket for you, with your reviews. There are two ways in which you can get authorization to download this. The ways to access this are explained [here](https://support.google.com/googleplay/android-developer/answer/6135870#export). To be able to use and deploy this script, you should create a Service Account, because you will need that JSON file for authentication
* Slackbot access
  * Create a bot for your Slack team and make a note of the generated token. More info [here](https://api.slack.com/bot-users)

# Setup
* Create a secrets.py file, using secrets-sample.py as example
  * Note: this contains the sensitive settings, that you probably want to keep encrypted
* Create a settings.py file, using settings-sample.py as example
  * Note: this contains the non-sensitive settings, that can be kept in plaintext 
* Run the script periodically! 

# How to deploy and run on AWS Lambda 

Coming soon! 


# License
Apache 2.0 - See [LICENSE] for more information.
