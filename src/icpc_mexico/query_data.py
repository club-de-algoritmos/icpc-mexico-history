from dataclasses import dataclass
from typing import Optional

from icpc_mexico.data import FinishedContest


@dataclass(frozen=True)
class ContestSeason:
    year: int
    qualifier: Optional[FinishedContest] = None
    regional: Optional[FinishedContest] = None
    world: Optional[FinishedContest] = None

    @property
    def name(self) -> str:
        return f'{self.year}-{self.year + 1}'
