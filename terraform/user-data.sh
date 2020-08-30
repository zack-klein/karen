#!/usr/bin/env bash

set -ex

sudo yum update -y
sudo yum install python3 -y
sudo pip3 install supervisor

# File variables
BUCKET=fantasy-football-streamlit
REQUIREMENTS_KEY=requirements.txt
APP_KEY=app.py

# Copy down requirments and app
sudo aws s3 cp s3://$BUCKET/$REQUIREMENTS_KEY ./$REQUIREMENTS_KEY
sudo aws s3 cp s3://$BUCKET/$APP_KEY ./$APP_KEY

# Install the requirements...
sudo pip3 install -r $REQUIREMENTS_KEY
STREAMLIT_PATH=$(which streamlit)
STREAMLIT_START_COMMAND="sudo $STREAMLIT_PATH run $APP_KEY --server.port 80"

# Set up supervisor to run the app in the background...
SUPERVISOR_PATH=$(which supervisord)
SUPERVISOR_LOG_FOLDER="/var/log/supervisord/"
SUPERVISOR_CONF_PATH="/home/ec2-user/supervisord.conf"
sudo mkdir -p $SUPERVISOR_LOG_FOLDER
printf "[supervisord]\nlogfile=$SUPERVISOR_LOG_FOLDER/supervisord.log\n\n" >> $SUPERVISOR_CONF_PATH
printf "[program:streamlit]\ncommand=$STREAMLIT_START_COMMAND" >> $SUPERVISOR_CONF_PATH
sudo $SUPERVISOR_PATH -c $SUPERVISOR_CONF_PATH
