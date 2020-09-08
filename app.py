import streamlit as st

from espn_api.football import League  # noqa:F401

from karen import utils, cleaning, constant


# Global configs - should never really change
YEARS = constant.SUPPORTED_YEARS
LOGO_URL = constant.LOGO_URL
APP_TITLE = constant.APP_TITLE
FAVICON = constant.FAVICON
st.beta_set_page_config(page_title=APP_TITLE, page_icon=FAVICON, layout="wide")


# TODO: Find a fix for this. Streamlit's `cache` function makes certain
# functions not importable by non-Streamlit processes. This is a hacky
# workaround.
@st.cache(
    suppress_st_warning=True,
    show_spinner=False,
    hash_funcs={League: lambda _: None},
)
def build_player_scores(current_week, league):
    return cleaning.build_player_scores(current_week, league)


# User-level settings - should change with every user/session in a browser.
year = st.sidebar.selectbox("Year:", YEARS)
league = utils.get_league(year)
teams = [t.team_name for t in league.teams]
power_rankings = league.power_rankings()
num_weeks = [i + 1 for i in range(league.current_week)]
week_min = min(num_weeks)
week_max = max(num_weeks)

# Dataframes for display/manipulation
# This contains the `player_df`, a large dataframe that gets cached to
# Streamlit's cache.
player_df = build_player_scores(league.current_week, league)


# Title section
st.title(f"Karen's Fantasy Outlook for {league.settings.name} ({year})")
st.image(LOGO_URL)

# Power rankings section
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
if week_min < week_max:
    for_week_pr = st.slider(
        "Week:",
        min_value=week_min,
        max_value=max(num_weeks),
        value=week_max,
        key="week-pr",
    )
else:
    for_week_pr = week_min

power_rankings_df = cleaning.build_power_rankings_df(league, for_week_pr)
st.table(power_rankings_df)

# Around the league section
st.write("## Around the league")

# Team level stats section
st.write("### Team Level Stats")

# If there has been more than 1 week, show a slider for week selection
if week_min < week_max:
    for_weeks_teams = st.slider(
        "For weeks:",
        min_value=week_min,
        max_value=max(num_weeks),
        value=(week_min, week_max),
        key="weeks-teams",
    )
else:
    for_weeks_teams = (week_min, week_max)

team_summary = cleaning.build_team_summary(
    player_df, week_range=for_weeks_teams
)

st.table(team_summary)

# Player level stats section
st.write("### Player Level Stats")

# If there has been more than 1 week, show a slider for week selection
if week_min < week_max:
    for_weeks_players = st.slider(
        "For weeks:",
        min_value=week_min,
        max_value=max(num_weeks),
        value=(week_min, week_max),
        key="weeks-players",
    )
else:
    for_weeks_players = (week_min, week_max)

on_teams = st.multiselect("For teams:", teams)
players_summary = cleaning.build_player_summary(
    player_df, week_range=for_weeks_players, on_teams=on_teams,
)
st.table(players_summary)

# Position level stats section
st.write("### Player Performance by Position")
position_stats_types = [
    "Most points scored",
    "Out-performed projection",
    "Under-performed projection",
]
position_stats_type = st.selectbox("Pick a statistic:", position_stats_types)

# If there has been more than 1 week, show a slider for week selection
if week_min < week_max:
    for_weeks_positions = st.slider(
        "For weeks:",
        min_value=week_min,
        max_value=max(num_weeks),
        value=(week_min, week_max),
        key="weeks-positions",
    )
else:
    for_weeks_positions = (week_min, week_max)

top_positions_df = cleaning.build_top_positions_df(
    player_df, week_range=for_weeks_positions, mode=position_stats_type
)
st.table(top_positions_df)

# Team Journeys section

st.write("## Team Journeys")
team_name = st.selectbox("Team:", teams)
team = [t for t in league.teams if t.team_name == team_name][0]
st.write(f"### {team.team_name} ({team.wins}-{team.losses})")
team_df = cleaning.build_team_df_w_results(team.team_name, player_df)
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
    **{team.team_name}** currently has a record of **{team.wins}** wins and
    **{team.losses}** losses. **{unexpected_outcomes}** of these
    **{team.wins + team.losses}** outcomes can be considered unexpected
    (the actual result was different than the projected result), with
    **{unexpected_wins}** unexpected wins and **{unexpected_losses}**
    unexpected losses.

    This team has generally been **{favored}** by unexpected outcomes this
    season.
"""
st.write(TEXT)
fig = cleaning.build_projected_vs_actual_chart(team_df)
mvp_fig = cleaning.build_mvp_chart(team.team_name, player_df)

st.write(fig)

st.write("## MVP Analysis")

team_df = player_df[player_df["Team"] == team.team_name]
team_df.sort_values("Cumulative Score", ascending=False, inplace=True)

top_player = team_df["Player Name"].values[0]
top_player_points = team_df["Cumulative Score"].values[0]
total_points = team.points_for
top_players_points = sum(team_df["Cumulative Score"].values[0:3])
top_player_points_pcent = round(top_player_points / total_points, 2) * 100
top_players_pcent = round(top_players_points / total_points, 2) * 100
is_balanced = "top-heavy" if top_players_pcent > 50 else "balanced"

MVP_TEXT = f"""
    **{top_player}** is the MVP of **{team.team_name}** with
    **{top_player_points}** points scored. This amounts to around
    **{top_player_points_pcent}%** of {team.team_name}'s **{total_points}**
    points.

    All together, the top 3 players on {team.team_name} scored
    **{top_players_points}** points, which accounts for
    **{top_players_pcent}%** of {team.team_name}'s points, indicating a
    **{is_balanced}** team overall (a team is top-heavy if the top 3 players
    scored more than 50% of the team's points).

    The graph below shows each players contribution to the team's total score
    over time, with players that have a higher point contribution near the
    bottom.

"""

st.write(MVP_TEXT)
st.write(mvp_fig)


# Free agent recommendations
st.write("## Free Agent Recommendations (Beta)")
st.write(
    "Karen will only recommend free agent transactions for a team if:\n"
    "- They have a higher position ranking (according to ESPN)\n"
    "- They are projeted to score more points *this week*\n"
    "- They are projected to score more points *this year*\n"
)
fa_team_name = st.selectbox("Team:", teams, key="fa-teams")
fa_team = [t for t in league.teams if t.team_name == fa_team_name][0]

if team:
    import pandas as pd

    fa_recommendations = cleaning.get_recommendations(
        fa_team.team_name, league
    )
    if fa_recommendations:
        recommended_players = [p for p in fa_recommendations]
        fa_player = st.selectbox("Select a player:", recommended_players)

        if fa_player:
            recommended_actions = fa_recommendations[fa_player]
            rows = []
            for action in recommended_actions:
                swap_for = action["swap_for"]
                text = f"Swap {fa_player} for {swap_for}."
                why = ", ".join(action["for_reasons"])
                row = ["", text, why]
                rows.append(row)

            fa_df = pd.DataFrame(
                rows, columns=["Index", "Recommendation", "Reasons"]
            )
            fa_df.set_index("Index", inplace=True)
            st.table(fa_df)

    else:
        st.write(f"No recommendations here for {fa_team.team_name} :ok_hand:")
