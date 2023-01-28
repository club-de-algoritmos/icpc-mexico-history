from typing import List, Optional

from icpc_mexico.data import School, ContestType, FinishedContest, TeamResult
from icpc_mexico.utils import normalize_str


def get_school(school_name: str, schools: List[School]) -> Optional[School]:
    school_name = normalize_str(school_name)
    for school in schools:
        if school.matches_name(school_name):
            return school
    return None


def get_by_type(contest_type: ContestType, contests: List[FinishedContest]) -> Optional[FinishedContest]:
    for contest in contests:
        if contest.type == contest_type:
            return contest
    return None


def get_by_school(school: School, contest: FinishedContest) -> List[TeamResult]:
    return [team for team in contest.team_results if school.matches_name(team.institution)]


def get_best_by_school(school: School, contest: FinishedContest) -> Optional[TeamResult]:
    teams = get_by_school(school, contest)
    if teams:
        return teams[0]
    return None
