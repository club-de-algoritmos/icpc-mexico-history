from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional, List, Set

from dataclasses_json import dataclass_json

from icpc_mexico.utils import normalize_school_name

MEXICO = 'mexico'


@dataclass_json
class SchoolCommunity(str, Enum):
    TECNM = 'Tecnologico Nacional de Mexico'
    ITESM = 'Instituto Tecnologico y de Estudios Superiores de Monterrey'

    @property
    def abbreviation(self) -> str:
        if self == SchoolCommunity.TECNM:
            return 'TecNM'
        if self == SchoolCommunity.ITESM:
            return 'ITESM'
        raise ValueError(f'Unknown abbreviation for {self}')


@dataclass_json
@dataclass(frozen=True)
class School:
    # Most popular name (how people refer to this school, or the canonical name)
    name: str
    # Alternative names this school may be known as
    alt_names: List[str] = field(default_factory=list)
    # Community this school belongs to
    community: Optional[SchoolCommunity] = None
    country: Optional[str] = None
    state: Optional[str] = None
    # Whether this school is eligible for ICPC (not high school, not unknown, etc.)
    is_eligible: bool = True

    @property
    def names(self) -> Set[str]:
        return ({normalize_school_name(self.name)}
                | {normalize_school_name(alt_name) for alt_name in self.alt_names})

    def matches_name(self, name: str) -> bool:
        return normalize_school_name(name) in self.names


@dataclass_json
@dataclass(frozen=True)
class TeamResult:
    id: int
    name: str
    institution: str
    rank: Optional[int]
    problems_solved: Optional[int]
    total_time: Optional[int]
    last_problem_time: Optional[int]
    medal_citation: Optional[str]
    site_citation: Optional[str]
    citation: Optional[str]
    # Computed results:
    school: Optional[School] = None
    community_rank: Optional[int] = None
    country_rank: Optional[int] = None
    # TODO:
    # super_region: Optional[SuperRegion] = None
    # super_region_rank: Optional[int] = None


@dataclass_json
@dataclass(frozen=True)
class ContestSiteTeam:
    id: int
    name: str
    status: Optional[str]
    country: str
    institution: str


@dataclass_json
@dataclass(frozen=True)
class ContestSite:
    id: int
    name: str
    homepage: Optional[str]
    date: Optional[str]
    email: str
    type: str


class ContestType(str, Enum):
    PROGRAMMING_BATTLE = 'programming_battle'
    GRAN_PREMIO = 'gran_premio'
    REGIONAL = 'regional'
    CHAMPIONSHIP = 'championship'
    WORLD = 'world'

    def title(self) -> str:
        if self in [ContestType.PROGRAMMING_BATTLE, ContestType.GRAN_PREMIO]:
            return 'Clasificatorio'
        if self == ContestType.REGIONAL:
            return 'Regional'
        if self == ContestType.CHAMPIONSHIP:
            return 'Campeonato'
        if self == ContestType.WORLD:
            return 'Final Mundial'
        raise ValueError(f'Unknown contest type {self}')


@dataclass_json
@dataclass(frozen=True)
class Contest:
    id: int
    url_id: str
    name: str
    year: int
    date: str
    type: ContestType
    comments: str

    @property
    def season(self) -> str:
        return f'{self.year}-{self.year+1}'

    @property
    def is_manual(self) -> bool:
        return self.comments == 'Manual'


@dataclass_json
@dataclass(frozen=True)
class FinishedContest(Contest):
    team_results: List[TeamResult]

    @classmethod
    def from_contest(cls, contest: Contest, **kwargs):
        return cls(**asdict(contest), **kwargs)
