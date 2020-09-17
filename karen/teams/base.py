from abc import ABC, abstractmethod


class BaseTeam(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def build_unexpected_outcomes_df(self):
        pass

    @abstractmethod
    def build_unexpected_outcomes_chart(self):
        pass

    @abstractmethod
    def build_mvp_analysis_df(self):
        pass

    @abstractmethod
    def build_mvp_analysis_chart(self):
        pass

    @abstractmethod
    def build_free_agents_recommendations(self):
        pass
