#!/usr/bin/env bash

set -ex

sudo yum update -y
sudo yum install python3 -y
sudo pip3 install supervisor

# File variables
BUCKET=fantasy-football-streamlit
REQUIREMENTS_KEY=requirements.txt
APP_KEY=app.py
LOCAL_BASE_PATH="/home/ec2-user"
LOCAL_REQUIREMENTS_PATH="$LOCAL_BASE_PATH/$REQUIREMENTS_KEY"
LOCAL_APP_PATH="$LOCAL_BASE_PATH/$APP_KEY"

# Copy down requirments and app
sudo aws s3 cp s3://$BUCKET/$REQUIREMENTS_KEY $LOCAL_REQUIREMENTS_PATH
sudo aws s3 sync s3://$BUCKET/ "$LOCAL_BASE_PATH/" --delete

# Install the requirements...
sudo pip3 install -r $LOCAL_REQUIREMENTS_PATH
STREAMLIT_PATH=$(which streamlit)
STREAMLIT_START_COMMAND="sudo $STREAMLIT_PATH run $LOCAL_APP_PATH --server.port 443"

# Set up supervisor to run the app in the background...
SUPERVISOR_PATH=$(which supervisord)
SUPERVISOR_LOG_FOLDER="$LOCAL_BASE_PATH/supervisord/"
SUPERVISOR_CONF_PATH="$LOCAL_BASE_PATH/supervisord.conf"
sudo mkdir -p $SUPERVISOR_LOG_FOLDER
printf "[supervisord]\nlogfile=$SUPERVISOR_LOG_FOLDER/supervisord.log\n\n" >> $SUPERVISOR_CONF_PATH
printf "[program:streamlit]\ncommand=$STREAMLIT_START_COMMAND" >> $SUPERVISOR_CONF_PATH
sudo $SUPERVISOR_PATH -c $SUPERVISOR_CONF_PATH

# Set up a cron job so we don't need to tear down the instance to get a new version of the code
LOCAL_CRON_PATH="$LOCAL_BASE_PATH/sync_app.sh"
LOCAL_CRON_LOG_PATH="$LOCAL_BASE_PATH/log_sync_app.log"
echo "* * * * * aws s3 sync s3://$BUCKET/ $LOCAL_BASE_PATH/ --delete &>> $LOCAL_CRON_LOG_PATH" >> $LOCAL_CRON_PATH
crontab $LOCAL_CRON_PATH
