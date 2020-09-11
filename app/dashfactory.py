from datetime import datetime as dt

from dash import Dash

import dash_core_components as dcc
import dash_html_components as html
import pandas_datareader as pdr
from dash.dependencies import Input
from dash.dependencies import Output
from .Dashboard.Dash_fun import apply_layout_with_auth

from karen import cleaning


DEMO_GRAPH_URL = "/dash/graphs/"
UNEXPECTED_OUTCOMES_GRAPH_URL = "/dash/unexpected_outcomes/"


def create_demo_dash_app(server, appbuilder):
    layout = html.Div(
        [
            html.H1("Stock Tickers"),
            dcc.Dropdown(
                id="my-dropdown",
                options=[
                    {"label": "Coke", "value": "COKE"},
                    {"label": "Tesla", "value": "TSLA"},
                    {"label": "Apple", "value": "AAPL"},
                ],
                value="COKE",
            ),
            dcc.Graph(id="my-graph"),
        ],
        style={"width": "500"},
    )

    app = Dash(server=server, url_base_pathname=DEMO_GRAPH_URL)
    apply_layout_with_auth(app, layout, appbuilder)

    @app.callback(
        Output("my-graph", "figure"), [Input("my-dropdown", "value")]
    )
    def update_graph(selected_dropdown_value):
        df = pdr.get_data_yahoo(
            selected_dropdown_value, start=dt(2017, 1, 1), end=dt.now()
        )
        return {
            "data": [{"x": df.index, "y": df.Close}],
            "layout": {"margin": {"l": 40, "r": 0, "t": 20, "b": 30}},
        }

    return app.server


def create_unexpected_outcomes_graph(team, player_df, server, appbuilder):
    team_df = cleaning.build_team_df_w_results(team, player_df)
    fig = cleaning.build_projected_vs_actual_chart(team_df)
    layout = html.Div([dcc.Graph(figure=fig)], style={"width": "500"})
    app = Dash(server=server, url_base_pathname=UNEXPECTED_OUTCOMES_GRAPH_URL)
    apply_layout_with_auth(app, layout, appbuilder)
    return app.server
