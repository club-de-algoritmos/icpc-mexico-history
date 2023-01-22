from collections import defaultdict
from typing import List, Dict, Optional

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, TeamResult
from icpc_mexico.utils import normalize_str


def analyze(contests: List[FinishedContest]) -> None:
    print(f'Analyzing results...')

    print('Mexico in the World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.country != 'mexico':
                continue
            community_desc = f', {team.community}' if team.community else ''
            print(f'    {team.rank} ({team.country_rank}) {team.name} ({team.institution}{community_desc})')
    print()

    print('TecNM in World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        participated = False
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if not participated:
                participated = True
                print(f'  {contest.name}:')
            print(f'    {team.rank} ({team.country_rank}) {team.name} ({team.institution})')
    print()

    print('Top 20 TecNM in Mexico Finals:')
    for contest in contests:
        if contest.type != ContestType.REGIONAL:
            continue

        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 20:
                break
            print(f'    {team.rank} ({team.community_rank}) {team.name} ({team.institution})')
    print()

    print('Top 10 TecNM in Mexico Qualifiers:')
    for contest in contests:
        if contest.type not in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
            continue

        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 10:
                break
            print(f'    {team.rank} ({team.community_rank}) {team.name} ({team.institution})')
    print()


def _get_by_type(contest_type: ContestType, contests: List[FinishedContest]) -> Optional[FinishedContest]:
    for contest in contests:
        if contest.type == contest_type:
            return contest
    return None


def _get_best_by_school(school_name: str, contest: FinishedContest) -> Optional[TeamResult]:
    for team in contest.team_results:
        if normalize_str(team.institution) == normalize_str(school_name):
            return team
    return None


def analyze_school(school_name: str, all_contests: List[FinishedContest]) -> None:
    print(f'Results for school {school_name}:')
    contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
    for contest in all_contests:
        contests_by_year[contest.year].append(contest)

    for year, contests in contests_by_year.items():
        result_type = ''
        best_team = None

        regional = _get_by_type(ContestType.REGIONAL, contests)
        if regional:
            best_team = _get_best_by_school(school_name, regional)
            if best_team:
                result_type = 'Mexico Regional'

        if not best_team:
            qualifier = _get_by_type(ContestType.GRAN_PREMIO, contests)
            if not qualifier:
                qualifier = _get_by_type(ContestType.PROGRAMMING_BATTLE, contests)

            if qualifier:
                best_team = _get_best_by_school(school_name, qualifier)
                if best_team:
                    result_type = 'Mexico Qualifiers'

        wf_team = None
        world = _get_by_type(ContestType.WORLD, contests)
        if world:
            wf_team = _get_best_by_school(school_name, world)

        if not best_team and not wf_team:
            continue

        print(f'  {year}-{year+1}:')
        if best_team:
            print(f'    {best_team.rank} ({best_team.community_rank}) {best_team.name} ({result_type})')
        if wf_team:
            print('    Went to World Finals')

    print()
