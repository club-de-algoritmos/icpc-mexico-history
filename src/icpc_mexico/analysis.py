from collections import defaultdict
from typing import List, Dict, TextIO, Set, Callable, Optional, Union, Protocol, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.queries import get_by_type, get_best_by_school, get_school


class WriteLineFunction(Protocol):
    def __call__(self, line: str = '') -> None:
        pass


def analyze(contests: List[FinishedContest], schools: List[School], analysis_file: TextIO) -> None:
    print(f'Analyzing Mexico results')

    def write_line(line: str = '') -> None:
        analysis_file.write(line + '\n')

    write_line('# Resultados de México en el ICPC')
    write_line()

    write_line('## Final Mundial')
    write_line()
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        write_line(f'### {contest.description()}')
        for team in contest.team_results:
            if team.country != 'mexico':
                continue
            community_desc = f', {team.community}' if team.community else ''
            write_line(f'- #{team.rank} (#{team.country_rank} Mexico) (solved {team.problems_solved})'
                       f' {team.name} ({team.institution}{community_desc})')
        write_line()

    write_line('# Resultados del TecNM en el ICPC')
    write_line()

    write_line('## Final Mundial')
    write_line()
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue

        participated = False
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if not participated:
                participated = True
                write_line(f'### {contest.description()}')
                write_line()
            write_line(f'- #{team.rank} (#{team.country_rank} Mexico) (solved {team.problems_solved})'
                       f' {team.name} ({team.institution})')
        if participated:
            write_line()

    _analyze_team_rank(contests, write_line)

    write_line('## Top 20 en el regional de México')
    write_line()
    first_place_tecnm_school_names: Set[str] = set()
    first_place_tecnm_schools: List[School] = []
    for contest in contests:
        if contest.type != ContestType.REGIONAL:
            continue

        write_line(f'### {contest.description()}')
        write_line()
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
            write_line(f'- #{team.rank} (#{team.community_rank} TecNM) {team.name} ({team.institution})')
        write_line()

    write_line('## Top 10 en el clasificatorio de México')
    write_line()
    for contest in contests:
        if contest.type not in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
            continue

        write_line(f'### {contest.description()}')
        write_line()
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 10:
                break
            write_line(f'- #{team.rank} (#{team.community_rank} TecNM) {team.name} ({team.institution})')
        write_line()

    write_line(f'## Historial de cada primer lugar entre los TecNM ({len(first_place_tecnm_schools)}')
    write_line()
    for school in sorted(first_place_tecnm_schools, key=lambda s: s.name):
        _analyze_school(school, contests, write_line)


def _analyze_school(school: School, all_contests: List[FinishedContest], write_line: WriteLineFunction) -> None:
    write_line(f'### {school.name.title()}')
    write_line()
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
                result_type = 'Regional'

        if not best_team:
            qualifier = get_by_type(ContestType.GRAN_PREMIO, contests)
            if not qualifier:
                qualifier = get_by_type(ContestType.PROGRAMMING_BATTLE, contests)

            if qualifier:
                best_team = get_best_by_school(school, qualifier)
                if best_team:
                    result_type = 'Clasificatorio'

        wf_team = None
        world = get_by_type(ContestType.WORLD, contests)
        if world:
            wf_team = get_best_by_school(school, world)

        if not best_team and not wf_team:
            continue

        write_line(f'#### {year}-{year+1}')
        write_line()
        if best_team:
            community_rank = ''
            if best_team.community == SchoolCommunity.TECNM:
                community_rank = f' (#{best_team.community_rank} TecNM)'
            write_line(f'- #{best_team.rank}{community_rank} {best_team.name} ({result_type})')
        if wf_team:
            write_line(f'  - Avanzó a la final mundial (resolvió {wf_team.problems_solved})')
        write_line()


TeamRank = Tuple[float, FinishedContest, TeamResult]


def _analyze_team_rank(all_contests: List[FinishedContest], write_line: WriteLineFunction) -> None:
    honorable_teams: List[TeamRank] = []
    high_teams: List[TeamRank] = []
    for contest in all_contests:
        if contest.type != ContestType.WORLD:
            continue

        last_rank = 0
        for team in contest.team_results:
            last_rank = max(last_rank, team.rank)

        team_count = len(contest.team_results)
        for team in contest.team_results:
            if team.country != MEXICO or not team.problems_solved:
                continue

            percentile = (team_count - team.rank) / (team_count - 1)
            team_values = (percentile, contest, team)
            if team.rank == last_rank or percentile < 0.5:
                honorable_teams.append(team_values)
            else:
                high_teams.append(team_values)

    def team_sort(team_rank: TeamRank) -> Tuple:
        percentile, contest, team = team_rank
        return 1 - percentile, team.rank, -team.problems_solved, contest.year, team.name
    honorable_teams.sort(key=team_sort)
    high_teams.sort(key=team_sort)

    def print_team(team_rank: TeamRank) -> None:
        percentile, contest, team = team_rank
        perc = round(percentile * 100)
        write_line(f'- {perc}% {team.name} ({team.institution}), '
                   f'resolvió {team.problems_solved} en {contest.year+1}, obteniendo el lugar #{team.rank}')

    write_line('## Ranking de equipos')
    write_line()

    write_line('### Sobresalientes')
    write_line()
    for team in high_teams:
        print_team(team)
    write_line()

    write_line('### Mención honorífica')
    write_line()
    for team in honorable_teams:
        print_team(team)
    write_line()
