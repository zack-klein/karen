import pandas as pd

from karen import cleaning


class BaseTeam(object):
    pass


class EspnTeam(BaseTeam):
    def __init__(
        self,
        team_name,
        year,
        league=None,
        unexpected_outcomes_df=None,
        mvp_analysis_df=None,
        free_agents_recommendations=None,
        setup_league=True,
        setup_unexpected_outcomes_df=True,
        setup_mvp_analysis_df=True,
        setup_free_agents_recommendations=True,
    ):
        self.team_name = team_name
        self.year = year
        self.league = league  # TODO

        if setup_unexpected_outcomes_df:
            self.unexpected_outcomes_df = self.get_unexpected_outcomes_df()
        else:
            self.unexpected_outcomes_df = unexpected_outcomes_df

        if setup_mvp_analysis_df:
            self.mvp_analysis_df = self.get_mvp_analysis_df()
        else:
            self.mvp_analysis_df = mvp_analysis_df

    def to_json(self):
        as_json = {
            "team_name": self.team_name,
            "year": self.year,
            "league": None,
            "unexpected_outcomes_df": self.unexpected_outcomes_df.to_json(),
            "mvp_analysis_df": self.mvp_analysis_df.to_json(),
            "free_agents_recommendations": self.free_agents_recommendations.to_json(),  # noqa:E501
            "setup_unexpected_outcomes_df": False,
            "setup_mvp_analysis_df": False,
            "setup_free_agents_recommendations": False,
        }
        return as_json

    def get_unexpected_outcomes_df(self):
        unexpected_outcomes_df = cleaning.build_team_df_w_results(
            self.team_name, self.league.player_df
        )
        return unexpected_outcomes_df

    def get_unexpected_outcomes_chart(self):
        chart = cleaning.build_projected_vs_actual_chart(
            self.unexpected_outcomes_df
        )
        return chart

    def get_mvp_analysis_df(self):
        mvp_analysis_df = cleaning.build_mvp_chart(
            self.team_name, self.league.player_df
        )
        return mvp_analysis_df

    def get_mvp_analysis_chart(self):
        chart = cleaning.build_mvp_chart(self.team_name, self.league.player_df)
        return chart

    def get_free_agents_recommendations(self):

        league = self.league.get_league()

        free_agents_recommendations = cleaning.get_free_agents_df(
            self.team_name, league
        )
        return free_agents_recommendations


def get_team(team_name, year, league, from_json=None):
    """
    """
    if from_json:
        team_args = pd.read_json(from_json)
        team = EspnTeam(**team_args)
    else:
        team = EspnTeam(team_name, year, league)
    return team
