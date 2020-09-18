import os

import streamlit as st

from karen import get_streamlit_app


platform = os.environ.get("KAREN_PLATFORM", "ESPN")
league_id = os.environ.get("KAREN_LEAGUE_ID", 503767)
secret_name = os.environ.get("KAREN_SECRET_NAME", "fantasy-football-secrets")


app = get_streamlit_app(st, platform, league_id, secret_name)
