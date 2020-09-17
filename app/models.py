from flask_appbuilder import Model

from sqlalchemy import Column, Integer, String, Boolean


class EspnLeague(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    league_id = Column(Integer, unique=True, nullable=False)
    secret_name = Column(String, nullable=False)
    power_rankings = Column(Boolean)
    team_level_stats = Column(Boolean)
    player_level_stats = Column(Boolean)
    player_position_stats = Column(Boolean)
    unexpected_outcomes = Column(Boolean)
    mvp_analysis = Column(Boolean)
    free_agent_recs = Column(Boolean)
    team_level_analytics = Column(Boolean)

    def __repr__(self):
        return self.name
