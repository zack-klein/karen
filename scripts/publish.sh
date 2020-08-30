set -ex

BUCKET=fantasy-football-streamlit
REQUIREMENTS_KEY=requirements.txt
APP_KEY=app.py
UNIQUE_KEY="$(date +%s).py"

aws s3 cp $REQUIREMENTS_KEY s3://$BUCKET/$REQUIREMENTS_KEY
aws s3 cp $APP_KEY s3://$BUCKET/$APP_KEY
aws s3 cp $APP_KEY s3://$BUCKET/$UNIQUE_KEY
