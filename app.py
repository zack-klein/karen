import json

import boto3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

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


def build_score_df(team, current_week):
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


def get_projected_points(lineup):
    """
    Build projected points from a lineup.
    """
    projected = 0

    for player in lineup:

        if player.slot_position != "BE":
            projected += player.projected_points

    return projected


def build_team_df(team, current_week, league):
    """
    Build a nice clean df of a given team's data.

    :param Team team: Team object.
    """
    columns = [
        "Index",
        "Week",
        "Projected Points",
        "Points Scored",
        "Projection Diff",
        "Opponent Projected Score",
        "Projected Result",
        "Result",
        "Lost/Won By",
        "Opponent",
        "Power Ranking",
        "Power Ranking Score",
    ]
    team_data = []

    bar = st.progress(0.0)

    for i in range(1, current_week + 1):

        print(f"Evaluating week {i}...")
        progress = i / len([i for i in range(current_week)])
        bar.progress(progress)

        score = team.scores[i - 1]
        diff = team.mov[i - 1]
        result = "W" if diff > 0 else "L"
        opponent = team.schedule[i - 1].team_name

        # Get the ranking for the current week
        rankings = league.power_rankings(week=i)
        for j, ranking in enumerate(rankings):
            ranked_team = ranking[1]

            if ranked_team.team_id == team.team_id:
                # league_ranking = ranked_team.standing
                power_ranking = j
                power_ranking_score = ranking[0]

        # Get the projected total
        box_scores = league.box_scores(week=i)
        for k, box_score in enumerate(box_scores):
            # Figure out if this team was home or away
            if box_score.away_team == 0:
                box_score.away_team = box_score.home_team

            elif box_score.home_team == 0:
                box_score.home_team = box_score.away_team

            if box_score.away_team.team_id == team.team_id:
                projected = get_projected_points(box_score.away_lineup)
                opp_projected = get_projected_points(box_score.home_lineup)

                if projected > opp_projected:
                    projected_result = "W"
                elif projected < opp_projected:
                    projected_result = "L"
                else:
                    projected_result = "T"

                break
            elif box_score.home_team.team_id == team.team_id:
                projected = get_projected_points(box_score.home_lineup)
                opp_projected = get_projected_points(box_score.away_lineup)

                if projected > opp_projected:
                    projected_result = "W"
                elif projected < opp_projected:
                    projected_result = "L"
                else:
                    projected_result = "T"

                break
            else:
                pass

        row = [
            "",
            i,
            projected,
            score,
            score - projected,
            opp_projected,
            projected_result,
            result,
            diff,
            opponent,
            power_ranking,
            power_ranking_score,
        ]
        team_data.append(row)

    team_df = pd.DataFrame(team_data, columns=columns)
    team_df.set_index("Index", inplace=True)
    return team_df


def build_projected_vs_actual_chart(df):
    """
    Build a plotly chart of Projected vs. Actual points
    that highlights unforeseen outcomes.
    """

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Week"],
            y=df["Projected Points"],
            fill="tozeroy",
            name="Projected Points",
            text=df["Projected Result"],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Week"],
            y=df["Points Scored"],
            fill="tonexty",
            name="Actual Points",
            text=df["Result"],
        )
    )

    for i, row in df.iterrows():
        week = row["Week"]
        proj_result = row["Projected Result"]
        act_result = row["Result"]
        if proj_result != act_result:

            fig.add_annotation(x=week, y=row["Points Scored"], text=act_result)
    return fig


LOGO_URL = "https://vignette.wikia.nocookie.net/spongebob/images/1/18/Karen-blue-form-stock-art.png/revision/latest?cb=20200317150606"  # noqa:E501
SECRETS = get_secrets()

YEARS = [2020, 2019, 2018, 2017, 2016, 2015]

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


if year >= 2019:

    # Team Journeys

    st.write("## Team Journeys")
    TEAMS = [t.team_name for t in league.teams]
    team_name = st.selectbox("Team:", TEAMS)
    team = [t for t in league.teams if t.team_name == team_name][0]
    st.write(f"### {team.team_name} ({team.wins}-{team.losses})")  # noqa:E501
    # with st.spinner(f"Crunching {team.team_name}'s numbers... hang tight!"):
    score_df = build_score_df(team, league.current_week)
    team_df = build_team_df(team, league.current_week, league)

    # Build a paragraph of analysis.
    unexpected_df = team_df[team_df["Projected Result"] != team_df["Result"]]
    unexpected_outcomes = len(unexpected_df)
    unexpected_wins = len(unexpected_df[unexpected_df["Result"] == "W"])
    unexpected_losses = len(unexpected_df[unexpected_df["Result"] == "L"])

    if unexpected_wins > unexpected_losses:
        favored = "helped"

    elif unexpected_wins < unexpected_losses:
        favored = "hurt"

    else:
        favored = "neither helped nor hurt"

    TEXT = f"""
        {team.team_name} currently has a record of **{team.wins}** wins and
        **{team.losses}** losses. **{unexpected_outcomes}** of these
        {team.wins + team.losses} outcomes can be considered unexpected
        (the actual result was different than the projected result), with
        **{unexpected_wins}** unexpected wins and **{unexpected_losses}**
        unexpected losses.

        This team has generally been **{favored}** by unexpected outcomes this
        season.
    """
    st.write(TEXT)
    fig = build_projected_vs_actual_chart(team_df)

    st.write(fig)

else:
    st.write("## Team Journeys")
    st.write("Team journeys are only available for 2019 and on!")
