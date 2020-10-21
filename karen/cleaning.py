import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from scipy.stats import zscore

from karen import utils


def build_power_rankings_df(league, week):
    """
    Build a nice clean dataframe of the power rankings.
    """

    power_rankings = league.power_rankings(week=week)

    columns = [
        "Team",
        "Team ID",
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
            team.team_id,
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

    # Get the manually updated power rankings and filter it this year and week
    power_ranking_takes = utils.get_spreadsheet_takes()
    power_ranking_takes["Team ID"] = power_ranking_takes["Team ID"].astype(str)
    power_ranking_takes["Year"] = power_ranking_takes["Year"].astype(str)
    power_ranking_takes = power_ranking_takes[
        (power_ranking_takes["Year"] == str(league.year))
        & (power_ranking_takes["Week"] == str(week))
    ]

    # Join the two df's
    left = df
    right = power_ranking_takes
    left["Team ID"] = left["Team ID"].astype(str)

    merged_df = pd.merge(left, right, on=["Team ID"], how="left")

    # Remove unnecessary columns
    del merged_df["Team_y"]
    del merged_df["Year"]
    del merged_df["Week"]
    del merged_df["Team ID"]

    # Fill nulls
    merged_df.fillna("", inplace=True)

    # Sort the DF
    if len(merged_df["Jake's Ranking"].unique()) != 10:
        merged_df["Power Ranking"] = merged_df["Power Ranking"].astype(int)
        merged_df["League Ranking"] = merged_df["League Ranking"].astype(int)
        merged_df.sort_values(
            ["Power Ranking", "League Ranking"], ascending=True, inplace=True
        )

    else:
        merged_df["Jake's Ranking"] = merged_df["Jake's Ranking"].astype(int)
        merged_df["Power Ranking"] = merged_df["Power Ranking"].astype(int)
        merged_df["League Ranking"] = merged_df["League Ranking"].astype(int)
        merged_df.sort_values(
            ["Jake's Ranking", "Power Ranking", "League Ranking"],
            ascending=True,
            inplace=True,
        )

    # Rename the Team column and set a new index
    merged_df.set_index("Power Rank Index", inplace=True)
    merged_df["Team"] = merged_df["Team_x"]
    del merged_df["Team_x"]

    # Finally, reoder the columns and be done!
    order = [
        "Team",
        "Jake's Ranking",
        "Power Ranking",
        "League Ranking",
        "Jake's Analysis",
        "Record",
        "Points Scored",
        "Points Allowed",
        "Point Differential",
        "Power Ranking Score",
    ]

    return merged_df[order]


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


def cumulative_score(row, player_df):

    current_week = row["Week"]

    if current_week == min(player_df["Week"]):
        return row["Points"]

    else:
        cumulative_score = 0
        for i in range(current_week):
            week = i + 1
            filtered = player_df[
                (player_df["Week"] == week)
                & (player_df["Player Name"] == row["Player Name"])
            ]

            if filtered["Points"].empty:
                weekly_score = 0
            else:
                weekly_score = filtered["Points"].values[0]

            cumulative_score += weekly_score
        return cumulative_score


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

    df["Cumulative Score"] = df.apply(cumulative_score, args=[df], axis=1)

    bar.empty()
    return df


def build_mvp_chart(team, player_df):
    """
    """
    team_df = player_df[player_df["Team"] == team]
    team_df.sort_values("Cumulative Score", ascending=False, inplace=True)
    fig = px.area(
        team_df, x="Week", y="Cumulative Score", color="Player Name",
    )

    fig.update_layout(
        title="Team MVP's",
        xaxis_title="Week",
        yaxis_title="Cumulative Points",
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
        showlegend=False,
    )
    return fig


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
        "Most Under Projected",
        "Most Over Projected",
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


def get_recommendations(team_name, league):
    """
    Get a list of recommendations for free agent swaps.
    """
    fas = league.free_agents(size=200)
    free_agents = {}

    rows = []
    for agent in fas:
        row = []

        row.append(agent.name)
        row.append(agent.projected_points)
        row.append(agent.position)
        row.append(agent.posRank)

        rows.append(row)

        this_position_free_agents = free_agents.get(agent.position, [])
        this_position_free_agents.append(agent)
        free_agents[agent.position] = this_position_free_agents

    # Look for recommendations for a specific team
    recommendations = {}

    team = [t for t in league.teams if t.team_name == team_name][0]

    for player in team.roster:
        candidates = free_agents[player.position]

        player_projected_points = player.stats.get(
            league.current_week, {}
        ).get("projected_points")
        player.projected_points = player_projected_points

        # For now, don't mess with injured players
        if player.projected_points != 0.0:

            for candidate in candidates:
                recommendation = {}
                against_arguments = []
                for_arguments = []

                # If candidate has a higher position rank, add argue to swap
                if candidate.posRank == [] or candidate.posRank == 0:
                    candidate.posRank = player.posRank + 1

                if player.posRank == [] or player.posRank == 0:
                    player.posRank = candidate.posRank + 1

                if candidate.posRank < player.posRank:
                    for_arguments.append(
                        f"{candidate.name} has a higher position rank ({candidate.posRank}) than {player.name} ({player.posRank})"  # noqa:E501
                    )

                else:
                    against_arguments.append(
                        f"{candidate.name} has a lower position rank ({candidate.posRank}) than {player.name} ({player.posRank})"  # noqa:E501
                    )

                # If a candidate has more projected points for this week, argue
                # to swap
                if (
                    not candidate.projected_points
                    or not player.projected_points
                ):
                    against_arguments.append(
                        f"Neither {candidate.name} nor {player.name} are projected to score any points this week."  # noqa:E501
                    )

                elif candidate.projected_points > player.projected_points:
                    for_arguments.append(
                        f"{candidate.name} is projected to score more points this week ({candidate.projected_points}) than {player.name} ({player.projected_points})"  # noqa:E501
                    )

                else:
                    against_arguments.append(
                        f"{candidate.name} is projected to score fewer points this week ({candidate.projected_points}) than {player.name} ({player.projected_points})"  # noqa:E501
                    )

                # If a candidate has more points for season, argue to swap
                player_season_points = player.stats.get(0, {}).get(
                    "projected_points"
                )
                player.season_projected = player_season_points

                candidate_season_points = candidate.stats.get(0, {}).get(
                    "projected_points"
                )
                candidate.season_projected = candidate_season_points

                if candidate.season_projected > player.season_projected:
                    for_arguments.append(
                        f"{candidate.name} is projected to score more points this year ({candidate.season_projected}) than {player.name} ({player.season_projected})"  # noqa:E501
                    )

                else:
                    against_arguments.append(
                        f"{candidate.name} is projected to score fewer points this year ({candidate.season_projected}) than {player.name} ({player.season_projected})"  # noqa:E501
                    )

                if len(against_arguments) == 0:
                    # If fantasy pros recommends a candidate, argue for it
                    fantasy_pros_rec = utils.get_fantasy_pros_recommendation(
                        candidate.name, player.name
                    )

                    if fantasy_pros_rec != {}:

                        player_pcnt = fantasy_pros_rec[player.name]
                        candidate_pcnt = fantasy_pros_rec[candidate.name]
                        fantasy_pros_url = fantasy_pros_rec["url"]

                        if candidate_pcnt > player_pcnt:
                            for_arguments.append(
                                f"Fantasy pros would start {candidate.name} "
                                f"({candidate_pcnt}) over {player.name} "
                                f"({player_pcnt}) ({fantasy_pros_url})"
                            )
                        else:
                            against_arguments.append(
                                f"Fantasy pros would start {player.name} "
                                f"({player_pcnt}) over {candidate.name} "
                                f"({candidate_pcnt}) ({fantasy_pros_url})"
                            )
                    if len(against_arguments) == 0:
                        requires_action = True
                    else:
                        requires_action = False
                else:
                    requires_action = False

                arguments = ", ".join(for_arguments + against_arguments)

                recommendation = {
                    "swap_for": candidate.name,
                    "reasons": arguments,
                    "for_reasons": for_arguments,
                    "against_reasons": against_arguments,
                }

                if requires_action:
                    player_recommendations = recommendations.get(
                        player.name, []
                    )
                    player_recommendations.append(recommendation)
                    recommendations[player.name] = player_recommendations

    return recommendations


def get_free_agents_df(fa_team_name, league):
    fa_team = [t for t in league.teams if t.team_name == fa_team_name][0]

    fa_recommendations = get_recommendations(fa_team.team_name, league)
    recommended_players = [p for p in fa_recommendations]
    rows = []

    for player in recommended_players:
        recommended_actions = fa_recommendations[player]

        for action in recommended_actions:
            swap_for = action["swap_for"]
            text = f"Swap {player} for {swap_for}."
            why = ", ".join(action["for_reasons"])
            row = [f"{player}-{swap_for}", text, why]
            rows.append(row)

    fa_df = pd.DataFrame(rows, columns=["Index", "Recommendation", "Reasons"])
    fa_df.set_index("Index", inplace=True)
    return fa_df


def get_player_analysis_chart(player_name, df):
    # Player Level
    player = df[df["Player Name"] == player_name]
    # points = sum(player["Points"])
    # projected = sum(player["Projected Points"])
    # diff = sum(player["Projection Diff"])
    position = player["Position"].unique()[0]

    # League Level
    grouped = df.groupby(by=["Player Name", "Position"]).sum()

    # Zscores and aggregate
    zscores = (
        df.groupby(by=["Player Name", "Position"])
        .sum()
        .apply(zscore)[["Points", "Projected Points", "Projection Diff"]]
    )
    zscores.columns = ["Points_z", "Projected Points_z", "Projection Diff_z"]
    zscores.query("Position == 'RB'").sort_values("Points_z", ascending=True)
    left = grouped
    right = zscores
    merged = left.merge(right, on=["Player Name", "Position"])
    del merged["Week"]
    merged.sort_values(by="Projection Diff_z", ascending=False)

    # Grouped by week
    weekly_grouped = (
        df.query(f"Position == '{position}'")[
            ["Week", "Points", "Projected Points", "Projection Diff"]
        ]
        .groupby("Week")
        .mean()
    )
    weekly_grouped.columns = [
        "League Average Points",
        "League Average Projected",
        "League Average Projection Diff",
    ]

    # 3 line graphs:
    # - 1. This player's points vs. league average (by position?)
    # - 2. This player's projection vs. league average (by position?)
    # - 3. This player's projection diff vs. league average (by position?)
    merged_player = player.merge(weekly_grouped, on="Week")

    last_week_performance = merged_player[
        merged_player["Week"] == max(merged_player["Week"])
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=merged_player["Week"],
            y=merged_player["League Average Points"],
            fill="tozeroy",
            name="League Average Points",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=merged_player["Week"],
            y=merged_player["Points"],
            name=f"{player_name.title()}'s Points",
            text=merged_player["Points"],
        )
    )

    fig.add_trace(
        go.Scatter(
            x=merged_player["Week"],
            y=merged_player["Projected Points"],
            name=f"{player_name.title()}'s Projected Points",
            text=merged_player["Projected Points"],
        )
    )

    fig.add_annotation(
        x=max(last_week_performance["Week"]),
        y=max(last_week_performance["Points"]),
        text=f"{player_name}",
        showarrow=True,
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
    )

    fig.add_annotation(
        x=max(last_week_performance["Week"]),
        y=max(last_week_performance["League Average Points"]),
        text=f"Average points for {position}'s",
        showarrow=True,
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
    )

    fig.update_layout(
        title=f"{player_name}'s Points",
        xaxis_title="Week",
        yaxis_title="Points",
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
        width=900,
    )
    return fig


def luck(row, return_val="lucky"):
    won = row["Won"]
    points = row["Points"]
    avg_points = row["League Points"]

    if won and points < avg_points:
        lucky = 1
        unlucky = 0

    elif not won and points > avg_points:
        lucky = 0
        unlucky = 1

    else:
        lucky = 0
        unlucky = 0

    if return_val == "lucky":
        return lucky
    elif return_val == "unlucky":
        return unlucky


def build_luck_df(df):
    """
    Build a dataframe of Lucky and Unlucky teams.
    """
    # Grab the weekly average of points for the league
    weekly_averages_df = (
        df[df["Slot"] != "BE"]
        .groupby(["Week", "Team"], as_index=False)
        .sum()
        .groupby(["Week"])
        .mean()[["Points"]]
    )
    weekly_averages_df["League Points"] = weekly_averages_df["Points"]
    del weekly_averages_df["Points"]

    # Grab each team's points
    team_points_df = (
        df[df["Slot"] != "BE"]
        .groupby(["Week", "Team", "Opponent"], as_index=False)
        .sum()[["Week", "Team", "Points", "Opponent"]]
    )
    team_points_df["Team Points"] = team_points_df["Points"]
    del team_points_df["Points"]
    # Self join to get opponent points
    w_opponent_score = team_points_df.merge(
        team_points_df[["Week", "Opponent", "Team Points"]],
        left_on=["Week", "Team"],
        right_on=["Week", "Opponent"],
    )
    w_opponent_score["Won"] = (
        w_opponent_score["Team Points_x"] > w_opponent_score["Team Points_y"]
    )
    w_opponent_score["Opponent"] = w_opponent_score["Opponent_x"]
    w_opponent_score["Points"] = w_opponent_score["Team Points_x"]
    w_opponent_score["Opponent Points"] = w_opponent_score["Team Points_y"]
    del w_opponent_score["Team Points_x"]
    del w_opponent_score["Team Points_y"]
    del w_opponent_score["Opponent_x"]
    del w_opponent_score["Opponent_y"]
    teams_df = w_opponent_score[
        ["Week", "Team", "Opponent", "Points", "Opponent Points", "Won"]
    ]

    # Join them together
    joined_df = teams_df.merge(weekly_averages_df, on=["Week"])

    joined_df["Lucky Wins"] = joined_df.apply(luck, axis=1)
    joined_df["Unlucky Losses"] = joined_df.apply(
        luck, axis=1, return_val="unlucky"
    )
    return joined_df


def build_team_luck_chart(team_name, luck_df):

    luck_df_team = luck_df[luck_df["Team"] == team_name]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=luck_df_team["Week"],
            y=luck_df_team["Points"],
            name=f"{team_name}'s Points",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=luck_df_team["Week"],
            y=luck_df_team["Opponent Points"],
            name=f"Opponent's Points",
            text=f"Opponent's Points",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=luck_df_team["Week"],
            y=luck_df_team["League Points"],
            fill="tozeroy",
            name=f"League Average Points",
            text=f"League Average Points",
        )
    )

    for i, row in luck_df_team.iterrows():

        if row["Lucky Wins"] != 0:
            x = row["Week"]
            y = row["Points"]
            fig.add_annotation(
                x=x,
                y=y,
                text="Lucky win!!!",
                showarrow=True,
                font=dict(family="IBM Plex Sans", size=14, color="#262730"),
                align="center",
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
            )

        elif row["Unlucky Losses"] != 0:
            x = row["Week"]
            y = row["Points"]
            fig.add_annotation(
                x=x,
                y=y,
                text="Unlucky loss!",
                showarrow=True,
                font=dict(family="IBM Plex Sans", size=14, color="#262730"),
                align="center",
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
            )

    fig.update_layout(
        title=f"{team_name}'s Lucky Wins & Unlucky Losses",
        xaxis_title="Week",
        yaxis_title="Points",
        font=dict(family="IBM Plex Sans", size=14, color="#262730"),
        width=900,
    )
    return fig
