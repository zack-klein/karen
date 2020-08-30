import json

import boto3
import pandas as pd
import streamlit as st

from espn_api.football import League


def get_secrets(secret_name="fantasy-football-secrets", region="us-east-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region,)

    response = client.get_secret_value(SecretId=secret_name)
    secret_string = response.get("SecretString", "{}")
    secrets = json.loads(secret_string)
    return secrets


def build_power_rankings_df(power_rankings):
    """
    Build a nice clean dataframe of the power rankings.

    :param List[Tuple[float, Team]] power_rankings: A list of tuples of the
        teams 2-step dominance score, and the team object.
    """
    index = "Power Rank Index"
    columns = [
        "Team",
        "Power Rank Index",
        "Power Ranking",
        "League Ranking",
        "Record",
        "Points Scored",
        "Points Allowed",
        "Point Differential",
        "Power Ranking Score",
    ]
    power_ranking_list = []

    for i, ranking_tuple in enumerate(power_rankings):

        # Get the values for the rows
        two_step_score = ranking_tuple[0]
        team = ranking_tuple[1]
        record = f"{team.wins}-{team.losses}"
        differential = team.points_for - team.points_against
        differential_prefix = ""
        if team.points_for - team.points_against > 0:
            differential_prefix = "+"

        # Build the row
        row = [
            team.team_name,
            "",
            i + 1,
            team.standing,
            record,
            round(team.points_for, 0),
            round(team.points_against, 0),
            f"{differential_prefix}{differential}",
            two_step_score,
        ]
        power_ranking_list.append(row)

    df = pd.DataFrame(power_ranking_list, columns=columns)
    df.set_index(index, inplace=True)
    return df


def build_team_df(team, current_week):
    """
    Build a nice clean df of a given team's data.

    :param Team team: Team object.
    """
    columns = ["Week", "Points Scores"]
    team_data = []

    for i in range(1, current_week + 1):
        row = [
            i,
            team.scores[i - 1],
        ]
        team_data.append(row)

    team_df = pd.DataFrame(team_data, columns=columns)
    team_df.set_index("Week", inplace=True)
    return team_df


LOGO_URL = "https://vignette.wikia.nocookie.net/spongebob/images/1/18/Karen-blue-form-stock-art.png/revision/latest?cb=20200317150606"  # noqa:E501
SECRETS = get_secrets()

YEARS = [2019, 2018, 2017, 2016, 2015]

year = st.sidebar.selectbox("Year:", YEARS)

league = League(
    league_id=503767,
    year=year,
    username=SECRETS["espn_username"],
    password=SECRETS["espn_password"],
    espn_s2=SECRETS["espn_s2"],
    swid=SECRETS["espn_swid"],
)

st.title(f"Karen's Fantasy Outlook for {league.settings.name} ({year})")
st.image(LOGO_URL)

# Power rankings
st.write("## Power Rankings*")
st.write(  # noqa:E501
    """
*These power rankings are calculated using a two-step dominance matrix (you
can read more about this methodology
[here](https://www.katemarshallmaths.com/uploads/1/8/8/2/18821302/dominance_matrices.pdf)).
Effectively, it looks at who has beaten who, and calculates the "better" team
that way. If team A beats team C, and team C beats team D - team A has "two
step dominance" over team D.
"""
)

power_rankings = league.power_rankings()
power_rankings_df = build_power_rankings_df(power_rankings)

st.table(power_rankings_df)

# Around the league

st.write("## Around the league")
columns = [
    "Index",
    "Top Scorer",
    "Least Scorer",
    "Most Scored Against",
    "Top Score Week",
    "Least Score Week",
]
row = [
    "",
    f"{league.top_scorer().team_name} ({league.top_scorer().points_for})",
    f"{league.least_scorer().team_name} ({league.least_scorer().points_for})",
    f"{league.most_points_against().team_name} ({league.most_points_against().points_for})",  # noqa:E501
    f"{league.top_scored_week()[0].team_name} ({league.top_scored_week()[1]})",
    f"{league.least_scored_week()[0].team_name} ({league.least_scored_week()[1]})",  # noqa:E501
]
around_the_league_df = pd.DataFrame([row], columns=columns)
around_the_league_df.set_index("Index", inplace=True)
st.table(around_the_league_df)

# Team journies

st.write("## Team Journies")
TEAMS = [t.team_name for t in league.teams]
team_name = st.selectbox("Team:", TEAMS)
team = [t for t in league.teams if t.team_name == team_name][0]
st.write(
    f"### {team.team_name} is on a {team.streak_length} game {team.streak_type.lower()} streak."  # noqa:E501
)

with st.spinner(f"Crunching {team.team_name}'s numbers... hang tight!"):
    team_df = build_team_df(team, league.current_week)

st.area_chart(team_df)

st.write("More analysis coming soon!")
