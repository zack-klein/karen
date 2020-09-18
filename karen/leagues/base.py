from abc import ABC, abstractmethod


class BaseLeague(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def build_player_df(self):
        pass

    @abstractmethod
    def build_power_rankings_df(self):
        pass

    @abstractmethod
    def build_team_summary_df(self):
        pass

    @abstractmethod
    def build_player_summary_df(self):
        pass

    @abstractmethod
    def build_top_positions_df(self):
        pass

    @abstractmethod
    def build_teams(self):
        pass

    @abstractmethod
    def get_team(self):
        pass
