from dataclasses import dataclass
from typing import Optional, List

from icpc_mexico.data import FinishedContest, TeamResult, School
from icpc_mexico.utils import get_percentile


@dataclass(frozen=True)
class ExtendedTeamResult:
    team_result: TeamResult
    contest: FinishedContest

    @property
    def percentile(self) -> float:
        team_count = len(self.contest.team_results)
        return get_percentile(self.team_result.rank, team_count)


@dataclass(frozen=True)
class RankedTeam:
    name: str
    school: School
    qualifier_result: Optional[ExtendedTeamResult] = None
    regional_result: Optional[ExtendedTeamResult] = None
    world_result: Optional[ExtendedTeamResult] = None
    regional_season_rank: Optional[int] = None
    regional_season_percentile: Optional[float] = None


@dataclass(frozen=True)
class ContestSeason:
    year: int
    qualifier: Optional[FinishedContest]
    regional: Optional[FinishedContest]
    world: Optional[FinishedContest]
    teams: List[RankedTeam]

    @property
    def name(self) -> str:
        return f'{self.year}-{self.year + 1}'
