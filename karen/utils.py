import base64
import boto3
import gspread
import json
import pandas as pd
import tempfile

from espn_api.football import League


def get_secrets(secret_name, region="us-east-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)

    response = client.get_secret_value(SecretId=secret_name)
    secret_string = response.get("SecretString", "{}")
    secrets = json.loads(secret_string)
    return secrets


def get_league(year, league_id=503767, secret_name="fantasy-football-secrets"):
    """
    Get an espn_api.football.League object from the espn_api.
    """
    secrets = get_secrets(secret_name)
    league = League(
        league_id=league_id,
        year=year,
        username=secrets["espn_username"],
        password=secrets["espn_password"],
        espn_s2=secrets["espn_s2"],
        swid=secrets["espn_swid"],
    )
    return league


def get_spreadsheet_takes():
    """
    Get data from a google spreadsheet to be used for fantasy rankings.
    """
    with tempfile.NamedTemporaryFile() as f:
        secrets = get_secrets("fantasy-football-secrets")
        file_str = base64.b64decode(secrets["gcloud_service_file"])
        f.write(file_str)
        f.seek(0)
        gc = gspread.service_account(f.name)

        wks = gc.open("Power Rankings").sheet1

        data = wks.get_all_values()
        headers = data.pop(0)

        df = pd.DataFrame(data, columns=headers)
    return df
