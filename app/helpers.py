import logging
import os
import pandas as pd

from app import db

from .models import EspnLeague

from karen import cleaning, utils


def build_player_scores_cached(league_name, current_week=None):
    """
    Cached wrapper around get_player_scores.
    """
    league = db.session.query(EspnLeague).filter_by(name=league_name).first()

    # Set up the league object
    league_obj = utils.get_league(
        2019, league_id=league.league_id, secret_name=league.secret_name,
    )

    if not current_week:
        current_week = league_obj.current_week

    path_name = (
        f"./cache/{current_week}_{league_obj.year}_{league_obj.league_id}.csv"
    )

    if os.path.exists(path_name):
        logging.info("Found cached file! Reading from cache...")
        player_df = pd.read_csv(path_name)
    else:
        logging.warning("No cached file found! Writing from scratch...")
        player_df = cleaning.build_player_scores(current_week, league_obj)
        player_df.to_csv(path_name)

    logging.info("Player DF successfully loaded...")
    return player_df


# @cache.cached(key_prefix='power_rankings_df')
def build_power_rankings_df_cached(league, week):
    return cleaning.build_power_rankings_df(league, week)
