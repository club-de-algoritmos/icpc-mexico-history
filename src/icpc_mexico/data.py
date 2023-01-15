from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional, List, Any


@dataclass(frozen=True)
class TeamResult:
    id: int
    name: str
    institution: str
    rank: int
    problems_solved: int
    total_time: int
    last_problem_time: int
    medal_citation: Optional[str]
    site_citation: Optional[str]
    citation: Optional[str]


class ContestType(str, Enum):
    PROGRAMMING_BATTLE = 'programming_battle'
    GRAN_PREMIO = 'gran_premio'
    REGIONAL = 'regional'
    CHAMPIONSHIP = 'championship'
    WORLD = 'world'


@dataclass(frozen=True)
class Contest:
    id: int
    url_id: str
    name: str
    year: int
    date: str
    type: ContestType
    comments: str


@dataclass(frozen=True)
class FinishedContest(Contest):
    team_results: List[TeamResult]

    @classmethod
    def from_contest(cls, contest: Contest, **kwargs):
        return cls(**asdict(contest), **kwargs)
