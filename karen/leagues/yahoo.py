import base64
import tempfile

import yahoo_fantasy_api as yfa

from yahoo_oauth import OAuth2

from karen import utils
from karen.leagues.base import BaseLeague


class YahooLeague(BaseLeague):
    def __init__(
        self, league_id, year, secret_name, debug=False,
    ):
        self.league_id = league_id
        self.year = year
        self.secret_name = secret_name
        self.debug = debug

        # Can be set later
        self.oauth = None
        self.yahoo_league = None
        self.player_df = None
        self.power_rankings_df = None
        self.team_summary_df = None
        self.player_summary_df = None
        self.top_positions_df = None
        self.teams = None

    def _reconnect(self):
        self.oauth.refresh_access_token()

    def connect(self):
        secrets = utils.get_secrets(self.secret_name)
        # TODO: Add some checks that the credentials are valid
        secrets_file_text = base64.b64decode(secrets["yahoo_oauth_file"])

        with tempfile.NamedTemporaryFile() as f:
            f.write(secrets_file_text)
            f.seek(0)
            oauth = OAuth2(None, None, from_file=f.name)
            gm = yfa.Game(oauth, "nfl")
            lg = gm.to_league(self.league_id)
            self.oauth = oauth
            self.yahoo_league = lg
