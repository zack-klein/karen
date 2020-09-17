from flask import redirect
from flask_appbuilder import expose, has_access, ModelView, BaseView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from .Dashboard import Dash_App1, Dash_App2
from .models import EspnLeague

from . import appbuilder, db, dashfactory

from karen import (
    league as karen_league,
    constant,
    team as karen_team,
)


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

    # @has_access
    # @expose("demo/")
    # def demo(self):
    #     dashfactory.create_demo_dash_app(app, appbuilder)
    #     return self.render_template(
    #         "dash.html",
    #         dash_url=dashfactory.DEMO_GRAPH_URL,
    #         appbuilder=appbuilder,
    #     )

    # @has_access
    # @expose(
    #     "unexpected_outcomes/<string:league_name>/<int:year>/<string:team_name>"
    # )
    # def unexpected_outcomes(self, league_name, year, team_name):
    #     league = (
    #         db.session.query(EspnLeague).filter_by(name=league_name).first()
    #     )
    #     league2 = karen_league.get_league(
    #         year, league_id=league.league_id, secret_name=league.secret_name,
    #     )
    #     team = karen_team.get_team(team_name, year, league2)
    #     chart = team.get_unexpected_outcomes_chart()
    #     dashfactory.create_unexpected_outcomes_graph(
    #         chart, team_name, league_name, year, app, appbuilder
    #     )
    #     url = dashfactory.UNEXPECTED_OUTCOMES_GRAPH_URL.format(
    #         league=league_name, team=team_name, year=year,
    #     )
    #     return self.render_template(
    #         "dash.html", dash_url=url, appbuilder=appbuilder,
    #     )


class EspnLeagueView(ModelView):
    datamodel = SQLAInterface(EspnLeague)


class LeagueView(BaseView):
    route_base = "/leagues/"
    default_view = "dummy"

    @has_access
    @expose("/")
    def dummy(self):
        return redirect("/")

    @has_access
    @expose("/<string:league_name>/")
    def leagues(self, league_name):
        league = (
            db.session.query(EspnLeague).filter_by(name=league_name).first()
        )
        return self.render_template(
            "year_list.html", years=constant.SUPPORTED_YEARS, league=league,
        )

    @has_access
    @expose("/<string:league_name>/<int:year>")
    def league(self, league_name, year):
        # Grab the league info from the database
        league = (
            db.session.query(EspnLeague).filter_by(name=league_name).first()
        )
        league2 = karen_league.get_league(
            year, league_id=league.league_id, secret_name=league.secret_name,
        )
        # Format tables into HTML
        league.year = league2.year
        league.power_rankings_df = league2.power_rankings_df.to_html(
            classes="table table-bordered", header="true", index=False
        )
        league.team_summary_df = league2.team_summary_df.to_html(
            classes="table table-bordered", header="true", index=False
        )
        league.player_summary_df = league2.player_summary_df.to_html(
            classes="table table-bordered", header="true", index=False
        )
        league.top_positions_df = league2.top_positions_df.to_html(
            classes="table table-bordered", header="true", index=False
        )
        league.teams = league2.teams

        # Unexpected outcomes dash url
        league.unexpected_outcomes_url = dashfactory.DEMO_GRAPH_URL

        return self.render_template(
            "league.html", appbuilder=appbuilder, league=league,
        )

    @has_access
    @expose("/<string:league_name>/<int:year>/teams/<string:team_name>")
    def team(self, league_name, year, team_name):
        """
        """
        league = (
            db.session.query(EspnLeague).filter_by(name=league_name).first()
        )
        league2 = karen_league.get_league(
            year, league_id=league.league_id, secret_name=league.secret_name,
        )
        team = karen_team.get_team(team_name, year, league2)

        # Unexpected outcomes URL
        unexpected_outcomes_url = dashfactory.UNEXPECTED_OUTCOMES_GRAPH_URL.format(  # noqa:E501
            league=league_name, team=team_name, year=year,
        )

        # # Grab the free agents recommendations
        # free_agents_df = cleaning.get_free_agents_df(
        #     "Golladay Inn", league_obj
        # )
        # if free_agents_df is not None:
        #     free_agents_df = free_agents_df.to_html(
        #         classes="table table-bordered", header="true", index=False
        #     )
        # else:
        #     free_agents_df = "<p>Woah there, no recommendations found!</p>"
        # league.free_agents_df = free_agents_df
        return self.render_template(
            "team.html",
            league=league,
            team=team,
            unexpected_outcomes_url=unexpected_outcomes_url,
        )


db.create_all()


def add_league_views():
    leagues = db.session.query(EspnLeague).all()
    for league in leagues:
        # for year in constant.SUPPORTED_YEARS:
        appbuilder.add_link(
            f"{league.name}",
            href=f"/leagues/{league.name}/",
            category="Leagues",
            category_icon="fa-flag-o",
        )


add_league_views()
appbuilder.add_view_no_menu(LeagueView)
appbuilder.add_view_no_menu(MyDashAppGraph())
appbuilder.add_view_no_menu(LeagueGraphView())
appbuilder.add_link(
    "Dashboard Graph",
    href="/dashboard_graph/",
    icon="fa-list",
    category="Dash Demo",
    category_icon="fa-list",
)
appbuilder.add_view(
    EspnLeagueView, "ESPN", category="Integrations", category_icon="fa fa-plug"
)
