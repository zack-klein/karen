import pandas as pd
import plotly.graph_objects as go
import streamlit as st


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


def build_team_df(team_name, df):
    team_df = df

    team_df = (
        df[(df["Team"] == team_name) & (df["Slot"] != "BE")]
        .groupby(
            ["Team", "Week", "Team ID", "Opponent", "Opponent ID"],
            as_index=False,
        )
        .sum()
    )
    return team_df


def build_team_df_w_results(team_name, df):
    home_df = build_team_df(team_name, df)

    rows = []
    for i, row in home_df.iterrows():
        opponent_df = build_team_df(row["Opponent"], df)
        opponent_df = opponent_df[opponent_df["Week"] == row["Week"]]

        home_projected = row["Projected Points"]
        home_actual = row["Points"]

        if opponent_df.empty:
            opponent_projected = 0
            opponent_actual = 0
            opponent_projected_diff = 0
        else:
            opponent_projected = opponent_df["Projected Points"].values[0]
            opponent_actual = opponent_df["Points"].values[0]
            opponent_projected_diff = opponent_df["Projection Diff"].values[0]

        if home_projected > opponent_projected:
            projected_result = "W"
        elif home_projected < opponent_projected:
            projected_result = "L"
        else:
            projected_result = "T"

        if home_actual > opponent_actual:
            actual_result = "W"
        elif home_actual < opponent_actual:
            actual_result = "L"
        else:
            actual_result = "T"

        row = [
            row["Week"],
            opponent_actual,
            opponent_projected,
            opponent_projected_diff,
            projected_result,
            actual_result,
        ]
        rows.append(row)

    opponent_scores_df_columns = [
        "Week",
        "Opponent Points",
        "Opponent Projected Points",
        "Opponent Projection Diff",
        "Projected Result",
        "Result",
    ]

    opponents_df = pd.DataFrame(rows, columns=opponent_scores_df_columns)

    # Join the two
    left = home_df
    right = opponents_df

    combined_df = pd.merge(left, right, how="inner", on=["Week"])

    return combined_df


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
            y=df["Points"],
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

            fig.add_annotation(x=week, y=row["Points"], text=act_result)

    fig.update_layout(
        title="Unexpected Outcomes",
        xaxis_title="Week",
        yaxis_title="Points",
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
    )

    return fig


def build_player_scores(current_week, league):
    """
    Get a dataframe of the league's players performance.
    """
    columns = [
        "Index",
        "Week",
        "Player Name",
        "Points",
        "Projected Points",
        "Projection Diff",
        "Position",
        "Slot",
        "Team",
        "Team ID",
        "Opponent",
        "Opponent ID",
    ]
    players = []

    bar = st.progress(0.0)

    for i in range(1, current_week + 1):
        print(f"Building players for week: {i}...")
        progress = i / len([i for i in range(current_week)])
        bar.progress(progress)

        box_scores = league.box_scores(week=i)

        for box_score in box_scores:

            home_exists = True
            away_exists = True

            if box_score.away_team == 0:
                away_exists = False

            elif box_score.home_team == 0:
                home_exists = False

            if away_exists:

                if home_exists:
                    opponent = box_score.home_team.team_name
                    opponent_id = box_score.home_team.team_id
                else:
                    opponent = ""
                    opponent_id = ""

                for player in box_score.away_lineup:
                    row = [
                        "",
                        i,
                        player.name,
                        player.points,
                        player.projected_points,
                        player.points - player.projected_points,
                        player.position,
                        player.slot_position,
                        box_score.away_team.team_name,
                        box_score.away_team.team_id,
                        opponent,
                        opponent_id,
                    ]

                    players.append(row)

            if home_exists:

                if away_exists:
                    opponent = box_score.away_team.team_name
                    opponent_id = box_score.away_team.team_id
                else:
                    opponent = ""
                    opponent_id = ""

                for player in box_score.home_lineup:
                    row = [
                        "",
                        i,
                        player.name,
                        player.points,
                        player.projected_points,
                        player.points - player.projected_points,
                        player.position,
                        player.slot_position,
                        box_score.home_team.team_name,
                        box_score.home_team.team_id,
                        opponent,
                        opponent_id,
                    ]

                    players.append(row)

    df = pd.DataFrame(players, columns=columns)
    df.set_index("Index", inplace=True)
    bar.empty()
    return df


def build_team_summary(player_df, top=3, week_range=None):
    """
    Build a clean dataframe of the team summary.
    """

    if week_range:
        player_df = player_df[
            (player_df["Week"] >= week_range[0])
            & (player_df["Week"] <= week_range[1])
        ]

    # Bench points
    bench_points = (
        player_df[player_df["Slot"] == "BE"][["Team", "Points"]]
        .groupby(["Team"])
        .sum()
        .sort_values("Points", ascending=False)
    )

    # Projections
    projections = (
        player_df[player_df["Slot"] != "BE"][["Team", "Projection Diff"]]
        .groupby(["Team"])
        .sum()
        .sort_values("Projection Diff", ascending=False)
    )

    rows = []

    for i in range(0, top):

        from_bottom = len(projections) - 1 - i

        most_over_projected = f"{projections.index.values[i]} ({round(projections['Projection Diff'][i], 2)})"  # noqa:E501
        least_over_projected = f"{projections.index.values[from_bottom]} ({round(projections['Projection Diff'][from_bottom], 2)})"  # noqa:E501
        most_points_on_bench = f"{bench_points.index.values[i]} ({round(bench_points['Points'][i], 2)})"  # noqa:E501
        least_points_on_bench = f"{bench_points.index.values[from_bottom]} ({round(bench_points['Points'][from_bottom], 2)})"  # noqa:E501

        row = [
            i + 1,
            most_over_projected,
            least_over_projected,
            most_points_on_bench,
            least_points_on_bench,
        ]
        rows.append(row)

    headers = [
        "Rank",
        "Most Over Projected",
        "Most Under Projected",
        "Most Points Left on Bench",
        "Least Points left on Bench",
    ]

    league_overview_df = pd.DataFrame(rows, columns=headers)
    league_overview_df.set_index("Rank", inplace=True)
    return league_overview_df


def build_player_summary(player_df, top=10, week_range=None, on_teams=None):
    """
    Build a clean dataframe of player level information.
    """

    if week_range:
        player_df = player_df[
            (player_df["Week"] >= week_range[0])
            & (player_df["Week"] <= week_range[1])
        ]

    if on_teams:
        player_df = player_df[player_df["Team"].isin(on_teams)]

    # Most points for a certain player
    most_points = (
        player_df[["Player Name", "Points"]]
        .groupby("Player Name")
        .sum()
        .sort_values("Points", ascending=False)
    )

    # Beat the projection most often
    beat_projection = (
        player_df[["Player Name", "Projection Diff"]]
        .groupby("Player Name")
        .sum()
        .sort_values("Projection Diff", ascending=False)
    )

    headers = [
        "Rank",
        "Most Points",
        "Most Under Projected",
        "Most Over Projected",
    ]
    rows = []

    for i in range(0, top):

        from_bottom = len(most_points) - 1 - i
        most_points_total = f"{most_points.index.values[i]} ({round(most_points['Points'][i], 2)})"  # noqa:E501
        most_over_projected = f"{beat_projection.index.values[i]} ({round(beat_projection['Projection Diff'][i], 2)})"  # noqa:E501
        most_under_projected = f"{beat_projection.index.values[from_bottom]} ({round(beat_projection['Projection Diff'][from_bottom], 2)})"  # noqa:E501

        row = [
            i + 1,
            most_points_total,
            most_over_projected,
            most_under_projected,
        ]
        rows.append(row)

    df = pd.DataFrame(rows, columns=headers)
    df.set_index("Rank", inplace=True)
    return df


def build_top_positions_df(
    player_df, top=5, week_range=None, mode="Most points scored"
):
    """
    Build a dataframe of the top n players at each position.
    """

    if week_range:
        player_df = player_df[
            (player_df["Week"] >= week_range[0])
            & (player_df["Week"] <= week_range[1])
        ]

    positions = ["QB", "RB", "TE", "WR", "D/ST", "K"]
    rows = []

    for i in range(top):

        row = []
        row.append(i + 1)

        for position in positions:

            if mode == "Most points scored":
                sort_col = "Points"
                ascending = False
            elif mode == "Out-performed projection":
                sort_col = "Projection Diff"
                ascending = False
            elif mode == "Under-performed projection":
                sort_col = "Projection Diff"
                ascending = True

            position_df = (
                player_df[player_df["Position"] == position]
                .groupby("Player Name", as_index=False)
                .sum()
                .sort_values(sort_col, ascending=ascending)
            )

            name = position_df["Player Name"].values[i]
            points = round(position_df[sort_col].values[i], 2)

            to_add = f"{name} ({points})"

            row.append(to_add)

        rows.append(row)

    positions.insert(0, "Index")
    top_positions_df = pd.DataFrame(rows, columns=positions)
    top_positions_df.set_index("Index", inplace=True)

    return top_positions_df
