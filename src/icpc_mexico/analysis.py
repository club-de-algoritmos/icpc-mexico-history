from collections import defaultdict
from typing import List, Dict, TextIO, Set

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School
from icpc_mexico.queries import get_by_type, get_best_by_school, get_school


def analyze(contests: List[FinishedContest], schools: List[School], analysis_file: TextIO) -> None:
    print(f'Analyzing Mexico results')

    def write_line(line: str = '') -> None:
        analysis_file.write(line + '\n')

    write_line('Mexico in the World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        write_line(f'  {contest.description()}:')
        for team in contest.team_results:
            if team.country != 'mexico':
                continue
            community_desc = f', {team.community}' if team.community else ''
            write_line(f'    #{team.rank} (#{team.country_rank} Mexico) (solved {team.problems_solved})'
                       f' {team.name} ({team.institution}{community_desc})')
    write_line()

    write_line('TecNM in World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        participated = False
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if not participated:
                participated = True
                write_line(f'  {contest.description()}:')
            write_line(f'    #{team.rank} (#{team.country_rank} Mexico) (solved {team.problems_solved})'
                       f' {team.name} ({team.institution})')
    write_line()

    write_line('Top 20 TecNM in Mexico Finals:')
    first_place_tecnm_school_names: Set[str] = set()
    first_place_tecnm_schools: List[School] = []
    for contest in contests:
        if contest.type != ContestType.REGIONAL:
            continue

        write_line(f'  {contest.description()}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 20:
                break
            if team.community_rank == 1:
                school = get_school(team.institution, schools)
                if school.name not in first_place_tecnm_school_names:
                    first_place_tecnm_school_names.add(school.name)
                    first_place_tecnm_schools.append(school)
            write_line(f'    #{team.rank} (#{team.community_rank} TecNM) {team.name} ({team.institution})')
    write_line()

    write_line('Top 10 TecNM in Mexico Qualifiers:')
    for contest in contests:
        if contest.type not in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
            continue

        write_line(f'  {contest.description()}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 10:
                break
            write_line(f'    #{team.rank} (#{team.community_rank} TecNM) {team.name} ({team.institution})')
    write_line()

    write_line(f'History of each TecNM first place ({len(first_place_tecnm_schools)}:')
    for school in sorted(first_place_tecnm_schools, key=lambda s: s.name):
        analyze_school(school, contests, analysis_file)


def analyze_school(school: School, all_contests: List[FinishedContest], analysis_file: TextIO) -> None:
    def write_line(line: str = '') -> None:
        analysis_file.write(line + '\n')

    write_line(f'  {school.name.title()}:')
    contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
    for contest in all_contests:
        contests_by_year[contest.year].append(contest)

    for year, contests in contests_by_year.items():
        result_type = ''
        best_team = None

        regional = get_by_type(ContestType.REGIONAL, contests)
        if regional:
            best_team = get_best_by_school(school, regional)
            if best_team:
                result_type = 'Mexico Regional'

        if not best_team:
            qualifier = get_by_type(ContestType.GRAN_PREMIO, contests)
            if not qualifier:
                qualifier = get_by_type(ContestType.PROGRAMMING_BATTLE, contests)

            if qualifier:
                best_team = get_best_by_school(school, qualifier)
                if best_team:
                    result_type = 'Mexico Qualifiers'

        wf_team = None
        world = get_by_type(ContestType.WORLD, contests)
        if world:
            wf_team = get_best_by_school(school, world)

        if not best_team and not wf_team:
            continue

        write_line(f'    {year}-{year+1}:')
        if best_team:
            community_rank = ''
            if best_team.community == SchoolCommunity.TECNM:
                community_rank = f' (#{best_team.community_rank} TecNM)'
            write_line(f'      #{best_team.rank}{community_rank} {best_team.name} ({result_type})')
        if wf_team:
            write_line(f'      Went to World Finals (solved {wf_team.problems_solved})')

    write_line()
