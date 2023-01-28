from collections import defaultdict
from typing import List, Dict, Set, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.markdown import Markdown
from icpc_mexico.queries import get_by_type, get_best_by_school, get_school


def analyze(contests: List[FinishedContest], schools: List[School], analysis_markdown: Markdown) -> None:
    print(f'Analyzing Mexico results')

    with analysis_markdown.section('Resultados de México en el ICPC'):
        with analysis_markdown.section('Final Mundial'):
            for contest in contests:
                if contest.type != ContestType.WORLD:
                    continue

                with analysis_markdown.section(contest.description()):
                    for team in contest.team_results:
                        if team.country != 'mexico':
                            continue
                        community_desc = f', {team.community}' if team.community else ''
                        analysis_markdown.bullet_point(f'#{team.rank} (#{team.country_rank} de México, '
                                                       f'resolvió {team.problems_solved})'
                                                       f' {team.name} ({team.institution}{community_desc})')

        _analyze_team_rank(contests, analysis_markdown)

    with analysis_markdown.section('Resultados del TecNM en el ICPC'):
        with analysis_markdown.section('Final Mundial'):
            wf_tecnm_school_names: Set[str] = set()
            wf_tecnm_schools: List[School] = []
            for contest in contests:
                if contest.type != ContestType.WORLD:
                    continue

                participations = []
                for team in contest.team_results:
                    if team.community != SchoolCommunity.TECNM:
                        continue
                    participations.append(f'#{team.rank} (#{team.country_rank} de México, resolvió {team.problems_solved})'
                                          f' {team.name} ({team.institution})')

                    school = get_school(team.institution, schools)
                    if school.name not in wf_tecnm_school_names:
                        wf_tecnm_school_names.add(school.name)
                        wf_tecnm_schools.append(school)

                if participations:
                    with analysis_markdown.section(contest.description()):
                        for participation in participations:
                            analysis_markdown.bullet_point(participation)

        with analysis_markdown.section('Top 5 en el regional de México'):
            for contest in contests:
                if contest.type != ContestType.REGIONAL:
                    continue

                with analysis_markdown.section(contest.description()):
                    for team in contest.team_results:
                        if team.community != SchoolCommunity.TECNM:
                            continue
                        if team.community_rank > 5:
                            break
                        analysis_markdown.bullet_point(f'#{team.rank} (#{team.community_rank} de TecNM) {team.name} ({team.institution})')

        with analysis_markdown.section('Historial de cada TecNM que ha llegado a la final mundial'):
            for school in sorted(wf_tecnm_schools, key=lambda s: s.name):
                _analyze_school(school, contests, analysis_markdown)


def _analyze_school(school: School, all_contests: List[FinishedContest], analysis_markdown: Markdown) -> None:
    with analysis_markdown.collapsible(school.name.title()):
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

            with analysis_markdown.section(f'{year}-{year+1}'):
                if best_team:
                    community_rank = ''
                    if best_team.community == SchoolCommunity.TECNM:
                        community_rank = f' (#{best_team.community_rank} de TecNM)'
                    analysis_markdown.bullet_point(f'#{best_team.rank}{community_rank} {best_team.name} ({result_type})')
                if wf_team:
                    analysis_markdown.bullet_point(f'Avanzó a la final mundial, donde resolvió {wf_team.problems_solved} '
                                                   f'problemas',
                                                   indent=1)


TeamRank = Tuple[float, FinishedContest, TeamResult]


def _analyze_team_rank(all_contests: List[FinishedContest], analysis_markdown: Markdown) -> None:
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
        analysis_markdown.bullet_point(f'{perc}% {team.name} ({team.institution}), '
                                       f'resolvió {team.problems_solved} en {contest.year+1}, '
                                       f'obteniendo el lugar #{team.rank}')

    with analysis_markdown.section('Ranking de equipos'):
        with analysis_markdown.section('Sobresalientes'):
            for team in high_teams:
                print_team(team)

        with analysis_markdown.section('Mención honorífica'):
            for team in honorable_teams:
                print_team(team)
