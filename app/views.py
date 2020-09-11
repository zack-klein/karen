from flask import redirect
from flask_appbuilder import expose, has_access, ModelView, BaseView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from .Dashboard import Dash_App1, Dash_App2
from .models import EspnLeague

from . import app, appbuilder, db, helpers, dashfactory

from karen import utils, cleaning


class MyDashAppCallBack(BaseView):
    route_base = "/"

    @has_access
    @expose("/dashboard_callback/")
    def methoddash(self):
        return self.render_template(
            "dash.html", dash_url=Dash_App1.url_base, appbuilder=appbuilder
        )


class MyDashAppGraph(BaseView):
    route_base = "/"

    @has_access
    @expose("/dashboard_graph/")
    def methoddash(self):
        return self.render_template(
            "dash.html", dash_url=Dash_App2.url_base, appbuilder=appbuilder
        )


appbuilder.add_view_no_menu(MyDashAppCallBack())
appbuilder.add_link(
    "Dashboard Callback",
    href="/dashboard_callback/",
    icon="fa-list",
    category="Dash Demo",
    category_icon="fa-list",
)


class LeagueGraphView(BaseView):
    route_base = "/graphs/"

    @has_access
    @expose("demo/")
    def demo(self):
        dashfactory.create_demo_dash_app(app, appbuilder)
        return self.render_template(
            "dash.html",
            dash_url=dashfactory.DEMO_GRAPH_URL,
            appbuilder=appbuilder,
        )

    @has_access
    @expose("unexpected_outcomes/<string:league_name>/<string:team_name>")
    def unexpected_outcomes(self, league_name, team_name):
        player_df = helpers.build_player_scores_cached(league_name)
        dashfactory.create_unexpected_outcomes_graph(
            team_name, player_df, app, appbuilder
        )
        return self.render_template(
            "dash.html",
            dash_url=dashfactory.UNEXPECTED_OUTCOMES_GRAPH_URL,
            appbuilder=appbuilder,
        )


class EspnLeagueView(ModelView):
    datamodel = SQLAInterface(EspnLeague)


db.create_all()


class LeagueView(BaseView):
    route_base = "/league/"
    default_view = "dummy"

    @has_access
    @expose("/")
    def dummy(self):
        add_league_views()
        return redirect("/")

    @has_access
    @expose("/<string:league_name>/")
    def league(self, league_name):
        # Grab the league info from the database
        league = (
            db.session.query(EspnLeague).filter_by(name=league_name).first()
        )

        # Set up the league object
        league_obj = utils.get_league(
            2020, league_id=league.league_id, secret_name=league.secret_name,
        )
        teams = [t.team_name for t in league_obj.teams]
        league.league_obj = league_obj

        # Grab the power rankings dataframe
        power_rankings_df = helpers.build_power_rankings_df_cached(
            league_obj, 1
        )
        league.power_rankings_df = power_rankings_df.to_html(
            classes="table table-bordered", header="true", index=False
        )

        # Grab the player_df. This is the BIG BOY.
        player_df = helpers.build_player_scores_cached(
            league_name, current_week=league_obj.current_week
        )

        league_obj.player_df = player_df

        # Grab the team summary df
        team_summary_df = cleaning.build_team_summary(
            player_df, week_range=(1, 15)
        )
        league.team_summary_df = team_summary_df.to_html(
            classes="table table-bordered", header="true", index=False
        )

        # Grab the player summary df
        player_summary_df = cleaning.build_player_summary(
            player_df, week_range=(1, 15), on_teams=teams,
        )
        league.player_summary_df = player_summary_df.to_html(
            classes="table table-bordered", header="true", index=False
        )

        # Grab the player summary by position
        # position_stats_types = [
        #     "Most points scored",
        #     "Out-performed projection",
        #     "Under-performed projection",
        # ]
        top_positions_df = cleaning.build_top_positions_df(
            player_df, week_range=(1, 15), mode="Most points scored",
        )
        league.top_positions_df = top_positions_df.to_html(
            classes="table table-bordered", header="true", index=False
        )

        # Unexpected outcomes dash url
        league.unexpected_outcomes_url = dashfactory.DEMO_GRAPH_URL

        # Grab the free agents recommendations
        free_agents_df = cleaning.get_free_agents_df(
            "Golladay Inn", league_obj
        )
        if free_agents_df is not None:
            free_agents_df = free_agents_df.to_html(
                classes="table table-bordered", header="true", index=False
            )
        else:
            free_agents_df = "<p>Woah there, no recommendations found!</p>"
        league.free_agents_df = free_agents_df

        return self.render_template(
            "karen.html", appbuilder=appbuilder, league=league,
        )


def add_league_views():
    leagues = db.session.query(EspnLeague).all()
    for league in leagues:
        appbuilder.add_link(
            f"{league.name}",
            href=f"/league/{league.name}/",
            category="Leagues",
            category_icon="fa-flag-o",
        )


add_league_views()
appbuilder.add_view(
    LeagueView, "Refresh", category="Leagues", icon="fa-refresh"
)
appbuilder.add_view_no_menu(MyDashAppGraph())
appbuilder.add_view_no_menu(LeagueGraphView())
appbuilder.add_link(
    "Dashboard Graph",
    href="/dashboard_graph/",
    icon="fa-list",
    category="Dash Demo",
    category_icon="fa-list",
)
appbuilder.add_view(EspnLeagueView, "ESPN Leagues")
