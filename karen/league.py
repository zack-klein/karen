import datetime
import json
import pandas as pd
import os


# from abc import ABC, abstractmethod

from espn_api.football import League

from karen import cleaning, utils, constant, team


def _get_cache_path(league_id, year, week):
    if not os.path.exists(constant.CACHE_DIR):
        os.mkdir(constant.CACHE_DIR)

    return constant.CACHE_PATH.format(
        league_id=league_id, year=year, week=week,
    )


class BaseLeague(object):

    pass


class EspnLeague(BaseLeague):
    def __init__(
        self,
        league_id,
        year,
        username,
        password,
        espn_s2,
        espn_swid,
        debug,
        week=None,
        league=None,
        player_df=None,
        power_rankings_df=None,
        team_summary_df=None,
        player_summary_df=None,
        top_positions_df=None,
        teams=[],
        set_league=True,
        set_player_df=True,
        set_power_rankings_df=True,
        set_team_summary_df=True,
        set_player_summary_df=True,
        set_top_positions_df=True,
        set_teams=True,
        cache=True,
    ):
        self.league_id = league_id
        self.year = year
        self.username = username
        self.password = password  # Should this not happen?
        self.espn_s2 = espn_s2
        self.espn_swid = espn_swid
        self.debug = debug
        self.week = week

        if set_league:
            self.league = self.get_league()
        else:
            self.league = league

        if set_player_df:
            self.player_df = self.get_player_df(week=self.week)
        else:
            self.player_df = player_df

        if set_power_rankings_df:
            self.power_rankings_df = self.get_power_rankings_df(week=self.week)
        else:
            self.power_rankings_df = power_rankings_df

        if set_team_summary_df:
            self.team_summary_df = self.get_team_summary_df(week=self.week)
        else:
            self.team_summary_df = team_summary_df

        if set_player_summary_df:
            self.player_summary_df = self.get_player_summary_df()
        else:
            self.player_summary_df = player_summary_df

        if set_top_positions_df:
            self.top_positions_df = self.get_top_positions_df(week=self.week)
        else:
            self.top_positions_df = top_positions_df

        if set_teams:
            self.teams = self.get_teams()
        else:
            self.teams = teams

        if cache:
            self.dump_session()

    def get_league(self):
        league = League(
            league_id=self.league_id,
            year=self.year,
            username=self.username,
            password=self.password,
            espn_s2=self.espn_s2,
            swid=self.espn_swid,
            debug=self.debug,
        )
        return league

    def get_player_df(self, week=None):

        if not week:
            week = self.league.current_week

        player_df = cleaning.build_player_scores(week, self.league)

        return player_df

    def dump_session(self, path=None):
        session = {
            "league_id": self.league_id,
            "year": self.year,
            "username": None,  # self.username,
            "password": None,  # self.password,
            "espn_s2": self.espn_s2,
            "espn_swid": self.espn_swid,
            "debug": self.debug,
            "league": None,
            "set_league": False,
            "player_df": self.player_df.to_json(),
            "set_player_df": False,
            "power_rankings_df": self.power_rankings_df.to_json(),
            "set_power_rankings_df": False,
            "team_summary_df": self.team_summary_df.to_json(),
            "set_team_summary_df": False,
            "player_summary_df": self.player_summary_df.to_json(),
            "set_player_summary_df": False,
            "top_positions_df": self.top_positions_df.to_json(),
            "set_top_positions_df": False,
            "teams": self.teams,
            "set_teams": False,
            "cached_at": datetime.datetime.now().timestamp(),
        }

        if not path:
            path = _get_cache_path(self.league_id, self.year, self.week)

        with open(path, "w") as f:
            s = json.dumps(session)
            f.write(s)
            f.seek(0)

    def get_power_rankings_df(self, week=None):
        if not week:
            week = self.league.current_week

        if not self.league:
            self.league = self.get_league()

        power_rankings_df = cleaning.build_power_rankings_df(self.league, week)
        return power_rankings_df

    def get_team_summary_df(self, week=None):

        if not week:
            week = self.league.current_week

        team_summary_df = cleaning.build_team_summary(
            self.player_df, week_range=(0, week)
        )
        return team_summary_df

    def get_player_summary_df(self, week=None, on_teams=None):

        if not self.league:
            self.league = self.get_league()

        player_summary_df = cleaning.build_player_summary(
            self.player_df, week_range=week, on_teams=on_teams,
        )
        return player_summary_df

    def get_top_positions_df(self, week=None, mode="Most points scored"):

        top_positions_df = cleaning.build_top_positions_df(
            self.player_df, week_range=week, mode=mode,
        )
        return top_positions_df

    def get_teams(self):
        t = [{"name": t.team_name, "id": t.team_id} for t in self.league.teams]
        return t

    def get_team(self, team_name):
        return team.get_team(team_name, self.year, self)


def load_session(year, league_id, week=None, cache_timeout=300, path=None):

    if not path:
        path = _get_cache_path(league_id, year, week)

    try:
        with open(path) as f:
            s = f.read()
            session_data = json.loads(s)

        # Check if the cache is valid
        cached_time = datetime.datetime.fromtimestamp(
            session_data["cached_at"]
        )
        cache_expiration = cached_time + datetime.timedelta(
            seconds=cache_timeout
        )

        if datetime.datetime.now() > cache_expiration:
            raise RuntimeError("Cache is invalid!")

        # Deserialize the df's
        session_data["player_df"] = pd.read_json(session_data["player_df"])
        session_data["power_rankings_df"] = pd.read_json(
            session_data["power_rankings_df"]
        )
        session_data["team_summary_df"] = pd.read_json(
            session_data["team_summary_df"]
        )
        session_data["player_summary_df"] = pd.read_json(
            session_data["player_summary_df"]
        )
        session_data["top_positions_df"] = pd.read_json(
            session_data["top_positions_df"]
        )

        # Delete the cached stuff
        del session_data["cached_at"]

        return EspnLeague(**session_data)

    except FileNotFoundError:
        raise FileNotFoundError("Session not found!")


def _get_league(
    year,
    week=None,
    league_id=503767,
    secret_name="fantasy-football-secrets",
    debug=False,
    cached=False,
    session_path=None,
    cache_timeout=constant.CACHE_TIMEOUT,
):
    """
    Get an League object.
    """
    if cached:
        league = load_session(
            year,
            league_id,
            week=week,
            path=session_path,
            cache_timeout=cache_timeout,
        )

    else:
        secrets = utils.get_secrets(secret_name)
        league = EspnLeague(
            league_id,
            year,
            secrets["espn_username"],
            secrets["espn_password"],
            secrets["espn_s2"],
            secrets["espn_swid"],
            debug,
            week=week,
        )

    return league


def get_league(
    year,
    week=None,
    league_id=503767,
    secret_name="fantasy-football-secrets",
    debug=False,
    cached=True,
    session_path=None,
    cache_timeout=constant.CACHE_TIMEOUT,
):
    """
    """
    no_cache = False
    if cached:
        try:
            league = _get_league(
                year,
                week=week,
                league_id=league_id,
                secret_name=secret_name,
                debug=debug,
                cached=True,
                session_path=session_path,
                cache_timeout=cache_timeout,
            )
        except (FileNotFoundError, RuntimeError):
            print("No cache found...")
            no_cache = True

    if any([not cached, no_cache]):
        league = _get_league(
            year,
            week=week,
            league_id=league_id,
            secret_name=secret_name,
            debug=debug,
            cached=False,
            session_path=session_path,
        )
    return league
