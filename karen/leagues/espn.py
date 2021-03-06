from espn_api.football import League

from karen import cleaning, utils
from karen.leagues.base import BaseLeague
from karen.teams.espn import EspnTeam


class EspnLeague(BaseLeague):
    def __init__(
        self, league_id, year, secret_name, debug=False,
    ):
        self.league_id = league_id
        self.year = year
        self.secret_name = secret_name
        self.debug = debug

        # Can be set later
        self.espn_league = None
        self.player_df = None
        self.power_rankings_df = None
        self.team_summary_df = None
        self.player_summary_df = None
        self.top_positions_df = None
        self.teams = None
        self.player_analysis_chart = None
        self.luck_df = None

    def connect(self):
        secrets = utils.get_secrets(self.secret_name)
        # TODO: Add some check for keys in the secret string?
        league = League(
            league_id=self.league_id,
            year=self.year,
            username=secrets["espn_username"],
            password=secrets["espn_password"],
            espn_s2=secrets["espn_s2"],
            swid=secrets["espn_swid"],
            debug=self.debug,
        )
        self.espn_league = league

    def build_player_df(self, week=None):

        if not self.espn_league:
            self.connect()

        if not week:
            if self.espn_league.current_week < 15:
                week = self.espn_league.current_week - 1
            else:
                week = self.espn_league.current_week

        player_df = cleaning.build_player_scores(week, self.espn_league)

        self.player_df = player_df

    def build_power_rankings_df(self, week=None):

        if not self.espn_league:
            self.connect()

        if not week:
            week = self.espn_league.current_week

        power_rankings_df = cleaning.build_power_rankings_df(
            self.espn_league, week
        )
        self.power_rankings_df = power_rankings_df

    def build_team_summary_df(self, week=None):

        if not self.espn_league:
            self.connect()

        team_summary_df = cleaning.build_team_summary(
            self.player_df, week_range=week
        )
        self.team_summary_df = team_summary_df

    def build_player_summary_df(self, week=None, on_teams=None):

        if not self.espn_league:
            self.connect()

        player_summary_df = cleaning.build_player_summary(
            self.player_df, week_range=week, on_teams=on_teams,
        )
        self.player_summary_df = player_summary_df

    def build_top_positions_df(self, week=None, mode="Most points scored"):

        if not self.espn_league:
            self.connect()

        top_positions_df = cleaning.build_top_positions_df(
            self.player_df, week_range=week, mode=mode,
        )
        self.top_positions_df = top_positions_df

    def build_teams(self):
        t = [
            {"name": t.team_name, "id": t.team_id}
            for t in self.espn_league.teams
        ]
        self.teams = t

    def get_team(self, team_name):
        if not self.espn_league:
            self.connect()

        if not self.teams:
            self.build_teams()

        teams = [t["name"] for t in self.teams]

        if team_name not in teams:
            raise ValueError(
                f"{team_name} is not a valid team in this league!"
                f"\nMust be one of: {', '.join(teams)}"
            )
        else:
            return EspnTeam(team_name, self.year, self)

    def build_player_analysis_chart(self, player_name):

        if not self.espn_league:
            self.connect()

        chart = cleaning.get_player_analysis_chart(player_name, self.player_df)

        self.player_analysis_chart = chart

    def build_luck_df(self):
        self.luck_df = cleaning.build_luck_df(self.player_df)

    def luckiest(self):
        df = (
            self.luck_df.groupby(["Team"], as_index=False)
            .sum()[["Team", "Lucky Wins"]]
            .sort_values(by=["Lucky Wins", "Team"], ascending=False)
        )
        df.set_index("Team", inplace=True)
        return df

    def unluckiest(self):
        df = (
            self.luck_df.groupby(["Team"], as_index=False)
            .sum()[["Team", "Unlucky Losses"]]
            .sort_values(by=["Unlucky Losses", "Team"], ascending=False)
        )
        df.set_index("Team", inplace=True)
        return df

    def build_team_luck_chart(self, team_name):
        chart = cleaning.build_team_luck_chart(team_name, self.luck_df)
        return chart
