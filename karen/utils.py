import boto3
import json

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
