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

st.write(fig)
