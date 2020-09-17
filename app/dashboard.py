import dash
from dash import Dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html

from karen import league as karen_league

from .models import EspnLeague


def init_dashboards(server, db):
    """
    Create a Plotly Dash dashboard for a given team and year.
    """
    leagues = db.session.query(EspnLeague).all()
    dash_apps = []
    years = [2019, 2020]

    for league in leagues:

        for year in years:
            url = f"/graphs/{league.name}/{year}/"
            dash_app = Dash(server=server, routes_pathname_prefix=url,)

            # dash_app = dash.Dash(__name__)
            dash_app.config["suppress_callback_exceptions"] = True
            l = karen_league.get_league(  # noqa:E741
                year, league_id=league.league_id, cached=False
            )

            # Constant
            WEEK_MIN = 1
            WEEK_MAX = 15
            WEEKS = [w for w in range(WEEK_MIN, WEEK_MAX + 1)]
            teams = l.teams
            teams_options = [
                {"label": t["name"], "value": t["name"]} for t in teams
            ]
            default_team_name = teams_options[0]["value"]
            default_team = l.get_team(default_team_name)

            # Power rankings
            power_rankings_df = l.power_rankings_df
            power_ranking_cols = [
                {"name": c, "id": c, "type": "text"}
                for c in power_rankings_df.columns
            ]
            teams = [
                {"label": c, "value": c}
                for c in power_rankings_df["Team"].unique()
            ]
            power_rankings = html.Div(
                [
                    html.H2("Power Rankings"),
                    dcc.Slider(
                        id="power-rankings-week-slider",
                        min=WEEK_MIN,
                        max=WEEK_MAX,
                        step=1,
                        marks={w: f"Week {w}" for w in WEEKS},
                        value=l.league.current_week,
                    ),
                    dash_table.DataTable(
                        id="power-ranking-table",
                        columns=power_ranking_cols,
                        data=power_rankings_df.to_dict("records"),
                        style_cell={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "center",
                        },
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "Jake's Analysis"},
                                "textAlign": "left",
                            },
                        ],
                        style_as_list_view=True,
                        sort_action="native",
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("power-ranking-table", "data"),
                [Input("power-rankings-week-slider", "value")],
            )
            def update_power_ranking_table(value):
                power_rankings_df = l.get_power_rankings_df(week=value)
                return power_rankings_df.to_dict("records")

            # Team summaries
            team_summary_df = l.team_summary_df
            team_summary_cols = [
                {"name": c, "id": c, "type": "text"}
                for c in team_summary_df.columns
            ]
            around_the_league = html.Div(
                [
                    html.H2("Team Summary"),
                    dash_table.DataTable(
                        id="team-summary",
                        columns=team_summary_cols,
                        data=team_summary_df.to_dict("records"),
                        style_cell={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "center",
                        },
                        style_as_list_view=True,
                    ),
                ],
                style={"width": "500"},
            )

            # Player level stats
            player_summary_df = l.player_summary_df
            player_summary_cols = [
                {"name": c, "id": c, "type": "text"}
                for c in player_summary_df.columns
            ]
            player_summary = html.Div(
                [
                    html.H2("Player Summary"),
                    html.Label("Select a team:"),
                    dcc.Dropdown(
                        id="player-summary-teams",
                        options=teams_options,
                        value=None,
                        multi=True,
                    ),
                    dash_table(
                        id="player-summary",
                        columns=player_summary_cols,
                        data=player_summary_df.to_dict("records"),
                        style_cell={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "center",
                        },
                        style_as_list_view=True,
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("player-summary", "data"),
                [Input("player-summary-teams", "value")],
            )
            def update_player_summary(selected_dropdown_values):
                player_summary = l.get_player_summary_df(
                    on_teams=selected_dropdown_values
                )
                return player_summary.to_dict("records")

            # Top positions
            top_positions_df = l.top_positions_df
            top_positions_cols = [
                {"name": c, "id": c, "type": "text"}
                for c in top_positions_df.columns
            ]
            top_performance_options = [
                {"label": "Most points scored", "value": "Most points scored"},
                {
                    "label": "Out-performed projection",
                    "value": "Out-performed projection",
                },
                {
                    "label": "Under-performed projection",
                    "value": "Under-performed projection",
                },
            ]
            top_positions = html.Div(
                [
                    html.H2("Top Performances by Position"),
                    dcc.Dropdown(
                        id="top-performances-types",
                        options=top_performance_options,
                        value=top_performance_options[0]["value"],
                    ),
                    dash_table.DataTable(
                        id="top-performances",
                        columns=top_positions_cols,
                        data=top_positions_df.to_dict("records"),
                        style_cell={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "center",
                        },
                        style_as_list_view=True,
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("top-performances", "data"),
                [dash.dependencies.Input("top-performances-types", "value")],
            )
            def update_top_positions(value):
                top_positions_df = l.get_top_positions_df(mode=value)
                return top_positions_df.to_dict("records")

            # Unexpected outcomes
            unexpected_outcomes_chart = (
                default_team.get_unexpected_outcomes_chart()
            )

            unexpected_outcomes = html.Div(
                [
                    html.H2("Unexpected Outcomes"),
                    html.Label("Select a team:"),
                    dcc.Dropdown(
                        id="unexpected-outcomes-teams",
                        options=teams_options,
                        value=default_team_name,
                    ),
                    dcc.Graph(
                        id="unexpected-outcomes-chart",
                        figure=unexpected_outcomes_chart,
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("unexpected-outcomes-chart", "figure"),
                [Input("unexpected-outcomes-teams", "value")],
            )
            def update_unexpected_outcomes(selected_dropdown_value):
                team = l.get_team(selected_dropdown_value)
                unexpected_outcomes_chart = (
                    team.get_unexpected_outcomes_chart()
                )
                return unexpected_outcomes_chart

            # MVP Analysis
            mvp_analysis_chart = default_team.get_mvp_analysis_chart()
            mvp_analysis = html.Div(
                [
                    html.H2("MVP Analysis"),
                    html.Label("Select a team:"),
                    dcc.Dropdown(
                        id="mvp-analysis-teams",
                        options=teams_options,
                        value=default_team_name,
                    ),
                    dcc.Graph(
                        id="mvp-analysis-chart", figure=mvp_analysis_chart
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("mvp-analysis-chart", "figure"),
                [Input("mvp-analysis-teams", "value")],
            )
            def update_mvp_analysis(selected_dropdown_value):
                team = l.get_team(selected_dropdown_value)
                mvp_analysis_chart = team.get_mvp_analysis_chart()
                return mvp_analysis_chart

            # Free agent recommendations
            free_agents_recommendations = (
                default_team.get_free_agents_recommendations()
            )
            free_agent_cols = [
                {"name": c, "id": c, "type": "text"}
                for c in free_agents_recommendations.columns
            ]
            free_agents = html.Div(
                [
                    html.H2("Free Agent recommendations"),
                    html.Label("Select a team:"),
                    dcc.Dropdown(
                        id="free-agent-recommendations-teams",
                        options=teams_options,
                        value=default_team_name,
                    ),
                    dash_table.DataTable(
                        id="free-agent-recommendations",
                        columns=free_agent_cols,
                        data=free_agents_recommendations.to_dict("records"),
                        style_cell={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "center",
                        },
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "Reasons"},
                                "textAlign": "left",
                            },
                        ],
                        style_as_list_view=True,
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("free-agent-recommendations", "data"),
                [Input("free-agent-recommendations-teams", "value")],
            )
            def update_free_agent_df(selected_dropdown_value):
                team = l.get_team(selected_dropdown_value)
                free_agents_recommendations = (
                    team.get_free_agents_recommendations()
                )
                return free_agents_recommendations.to_dict("records")

            @dash_app.callback(
                Output("loading-output-1", "children"),
                [Input("free-agent-recommendations-teams", "value")],
            )
            def input_triggers_spinner(value):
                import time

                time.sleep(1)
                return value

            analyses = {
                "Power Rankings": power_rankings,
                "Around the League": around_the_league,
                "Player Summary": player_summary,
                "Top Position Performances": top_positions,
                "Unexpected Outcomes": unexpected_outcomes,
                "MVP Analysis": mvp_analysis,
                "Free Agent Recommendations": free_agents,
            }
            analysis_options = [{"label": a, "value": a} for a in analyses]

            main = html.Div(
                [
                    html.H1("Karen's Fantasy Outlook"),
                    html.Label("Select an analysis:"),
                    dcc.Dropdown(
                        id="analysis-options",
                        options=analysis_options,
                        value=analysis_options[0]["value"],
                    ),
                    dcc.Loading(
                        id="main-loading", type="dot", children=html.Div(),
                    ),
                ],
                style={"width": "500"},
            )

            @dash_app.callback(
                Output("main-loading", "children"),
                [Input("analysis-options", "value")],
            )
            def update_selected_analysis(selected_dropdown_value):
                return analyses[selected_dropdown_value]

            dash_app.layout = main

    return dash_apps
