from karen import cleaning
from karen.teams.base import BaseTeam


class EspnTeam(BaseTeam):
    def __init__(
        self, team_name, year, league,
    ):
        self.team_name = team_name
        self.year = year
        self.league = league

        # Can be set later
        self.team = None
        self.unexpected_outcomes_df = None
        self.unexpected_outcomes_text = None
        self.unexpected_outcomes_chart = None
        self.mvp_analysis_df = None
        self.mvp_analysis_text = None
        self.mvp_analysis_chart = None
        self.free_agents_recommendations = None

        # This class depends on the player_df...
        if self.league.player_df is None:
            self.league.build_player_df()

    def _set_team(self):
        team = [
            t
            for t in self.league.espn_league.teams
            if t.team_name == self.team_name
        ][0]
        self.team = team

    def build_unexpected_outcomes_df(self):
        unexpected_outcomes_df = cleaning.build_team_df_w_results(
            self.team_name, self.league.player_df
        )
        self.unexpected_outcomes_df = unexpected_outcomes_df

    def build_unexpected_outcomes_text(self):
        if not self.team:
            self._set_team()

        team = self.team

        team_df = cleaning.build_team_df_w_results(
            team.team_name, self.league.player_df
        )
        # Build a paragraph of analysis.
        unexpected_df = team_df[
            team_df["Projected Result"] != team_df["Result"]
        ]
        unexpected_outcomes = len(unexpected_df)
        unexpected_wins = len(unexpected_df[unexpected_df["Result"] == "W"])
        unexpected_losses = len(unexpected_df[unexpected_df["Result"] == "L"])

        if unexpected_wins > unexpected_losses:
            favored = "helped"

        elif unexpected_wins < unexpected_losses:
            favored = "hurt"

        else:
            favored = "neither helped nor hurt"

        unexpected_outcomes_text = f"""
            **{team.team_name}** currently has a record of **{team.wins}** wins
            and **{team.losses}** losses. **{unexpected_outcomes}** of these
            **{team.wins + team.losses}** outcomes can be considered unexpected
            (the actual result was different than the projected result), with
            **{unexpected_wins}** unexpected wins and **{unexpected_losses}**
            unexpected losses.

            This team has generally been **{favored}** by unexpected outcomes
            this season.
        """
        self.unexpected_outcomes_text = unexpected_outcomes_text

    def build_unexpected_outcomes_chart(self):
        chart = cleaning.build_projected_vs_actual_chart(
            self.unexpected_outcomes_df
        )
        self.unexpected_outcomes_chart = chart

    def build_mvp_analysis_df(self):

        mvp_analysis_df = cleaning.build_mvp_chart(
            self.team_name, self.league.player_df
        )
        self.mvp_analysis_df = mvp_analysis_df

    def build_mvp_analysis_text(self):

        if not self.team:
            self._set_team()

        team = self.team

        team_df = self.league.player_df[
            self.league.player_df["Team"] == team.team_name
        ]
        team_df.sort_values("Cumulative Score", ascending=False, inplace=True)

        top_player = team_df["Player Name"].values[0]
        top_player_points = team_df["Cumulative Score"].values[0]
        total_points = team.points_for
        top_players_points = sum(team_df["Cumulative Score"].values[0:3])
        top_player_points_pcent = (
            round(top_player_points / total_points, 2) * 100
        )
        top_players_pcent = round(top_players_points / total_points, 2) * 100
        is_balanced = "top-heavy" if top_players_pcent > 50 else "balanced"

        mvp_text = f"""
            **{top_player}** is the MVP of **{team.team_name}** with
            **{top_player_points}** points scored. This amounts to around
            **{top_player_points_pcent}%** of {team.team_name}'s
            **{total_points}** points.

            All together, the top 3 players on {team.team_name} scored
            **{top_players_points}** points, which accounts for
            **{top_players_pcent}%** of {team.team_name}'s points, indicating a
            **{is_balanced}** team overall (a team is top-heavy if the top 3
            players scored more than 50% of the team's points).

            The graph below shows each players contribution to the team's total
            score over time, with players that have a higher point contribution
            near the bottom.

        """
        self.mvp_analysis_text = mvp_text

    def build_mvp_analysis_chart(self):
        chart = cleaning.build_mvp_chart(self.team_name, self.league.player_df)
        self.mvp_analysis_chart = chart

    def build_free_agents_recommendations(self):
        free_agents_recommendations = cleaning.get_free_agents_df(
            self.team_name, self.league.espn_league
        )
        self.free_agents_recommendations = free_agents_recommendations

    def build_record(self):
        if not self.team:
            self._set_team()
        self.record = f"{self.team.wins}-{self.team.losses}"
