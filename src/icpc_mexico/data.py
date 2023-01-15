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

    @staticmethod
    def from_json(json: Any):
        return TeamResult(
            id=json['teamId'],
            name=json['teamName'],
            institution=json['institution'],
            rank=json['rank'],
            problems_solved=json['problemsSolved'],
            total_time=json['totalTime'],
            last_problem_time=json['lastProblemTime'],
            medal_citation=json['medalCitation'],
            site_citation=json['siteCitation'],
            citation=json['citation'],
        )


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

    @staticmethod
    def from_csv(csv_row):
        return Contest(
            id=int(csv_row['id']),
            url_id=csv_row['url_id'],
            name=csv_row['name'],
            year=int(csv_row['year']),
            date=csv_row['date'],
            type=ContestType(csv_row['type']),
            comments=csv_row['comments'],
        )


@dataclass(frozen=True)
class FinishedContest(Contest):
    team_results: List[TeamResult]

    @classmethod
    def from_contest(cls, contest: Contest, **kwargs):
        return cls(**asdict(contest), **kwargs)
