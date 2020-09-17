import streamlit as st

from espn_api.football import League  # noqa:F401

from karen import cleaning, constant, get_league
from karen.leagues.espn import EspnLeague


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


@st.cache(
    suppress_st_warning=True,
    show_spinner=False,
    hash_funcs={EspnLeague: lambda _: None},
)
def get_league_cached(platform, league_id, year, secret_name):
    league = get_league(platform, league_id, year, secret_name)
    league.connect()
    league.build_player_df()
    return league


# User-level settings - should change with every user/session in a browser.
year = st.sidebar.selectbox("Year:", YEARS)
full_league = get_league_cached(
    "ESPN", 503767, year, "fantasy-football-secrets"
)
league = full_league.espn_league
teams = [t.team_name for t in league.teams]
power_rankings = league.power_rankings()
num_weeks = [i + 1 for i in range(league.current_week)]
week_min = min(num_weeks)
week_max = max(num_weeks)

# Dataframes for display/manipulation
# This contains the `player_df`, a large dataframe that gets cached to
# Streamlit's cache.


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

full_league.build_power_rankings_df(week=for_week_pr)
st.table(full_league.power_rankings_df)

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

full_league.build_team_summary_df(week=for_weeks_teams)
st.table(full_league.team_summary_df)

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
full_league.build_player_summary_df(week=for_weeks_players, on_teams=on_teams)
st.table(full_league.player_summary_df)

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

full_league.build_top_positions_df(
    week=for_weeks_positions, mode=position_stats_type
)
st.table(full_league.top_positions_df)

# Team Journeys section

st.write("## Unexpected Outcomes")
team_name = st.selectbox("Team:", teams)

team = full_league.get_team(team_name)
team.build_record()
team.build_unexpected_outcomes_df()
team.build_unexpected_outcomes_text()
team.build_unexpected_outcomes_chart()

st.write(f"### {team.team_name} ({team.record})")
st.write(team.unexpected_outcomes_text)
st.write(team.unexpected_outcomes_chart)

# MVP Analysis Section
st.write("## MVP Analysis")
team.build_mvp_analysis_df()
team.build_mvp_analysis_text()
team.build_mvp_analysis_chart()
st.write(team.mvp_analysis_text)
st.write(team.mvp_analysis_chart)


# Free agent recommendations
st.write("## Free Agent Recommendations (Beta)")
st.write(
    "Karen will only recommend free agent transactions for a team if:\n"
    "- The FA has a higher position ranking (according to ESPN)\n"
    "- The FA is projeted to score more points *this week*\n"
    "- The FA is projected to score more points *this year*\n"
    "- [Fantasy Pros](https://www.fantasypros.com/nfl/start/) would start the "
    "the FA"
)
fa_team_name = st.selectbox("Team:", teams, key="fa-teams")
fa_team = full_league.get_team(fa_team_name)
fa_team.build_free_agents_recommendations()

if fa_team.free_agents_recommendations.empty:
    st.write(f"No recommendations for {fa_team_name} :ok_hand:")
else:
    st.table(fa_team.free_agents_recommendations)
