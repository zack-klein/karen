import base64
import boto3
import gspread
import json
import pandas as pd
import requests
import tempfile

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from espn_api.football import League


def get_secrets(secret_name, region="us-east-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)

    response = client.get_secret_value(SecretId=secret_name)
    secret_string = response.get("SecretString", "{}")
    secrets = json.loads(secret_string)
    return secrets


def get_league(
    year, league_id=503767, secret_name="fantasy-football-secrets", debug=False
):
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
        debug=debug,
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


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_fantasy_pros_recommendation(player1, player2):
    """
    """
    print("Fetching... ", player1, player2)
    player1_clean = (
        player1.lower().replace(" jr.", "").replace(" ", "-").replace(".", "")
    )  # noqa:E501
    player2_clean = (
        player2.lower().replace(" jr.", "").replace(" ", "-").replace(".", "")
    )  # noqa:E501
    url = f"https://www.fantasypros.com/nfl/start/{player1_clean}-{player2_clean}.php"  # noqa:E501
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    recommendation = {}
    rec_span = soup.find_all(name="span", attrs={"class": "more"})
    not_rec_span = soup.find_all(name="span", attrs={"class": "same"})
    spans = soup.find_all(name="div", attrs={"class": "player-photo"})

    if rec_span and not_rec_span and spans:

        img = spans[0].find(name="img")
        recommended_player_text = img["alt"]
        recommended_player_pcnt = rec_span[0].text

        recommended_player_text_1 = similar(recommended_player_text, player1)
        recommended_player_text_2 = similar(recommended_player_text, player2)

        if recommended_player_text_1 > recommended_player_text_2:
            recommended_player = player1
            second_player = player2
        else:
            recommended_player = player2
            second_player = player1

        recommendation[recommended_player] = recommended_player_pcnt
        second_player_pcnt = not_rec_span[0].text
        recommendation[second_player] = second_player_pcnt

        recommendation["url"] = url

    return recommendation
