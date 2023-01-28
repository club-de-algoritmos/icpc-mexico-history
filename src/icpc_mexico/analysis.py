import os
from collections import defaultdict
from typing import List, Dict, Set, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import get_by_type, get_best_by_school, get_school
from icpc_mexico.utils import normalize_as_filename

TeamRank = Tuple[float, FinishedContest, TeamResult]


class Analyzer:
    def __init__(self, contests: List[FinishedContest], schools: List[School], analysis_path: str):
        self.contests = contests
        self.schools = schools
        self.analysis_path = analysis_path

    def _get_filename(self, *filepath: str) -> str:
        return os.path.join(self.analysis_path, *filepath)

    def analyze(self) -> None:
        self._analyze_world_finals()
        self._analyze_community(SchoolCommunity.TECNM, 'TecNM')

        mexican_schools = [school for school in self.schools if school.country == MEXICO]
        print(f'Analyzing {len(mexican_schools)} Mexican schools')
        for school in mexican_schools:
            self._analyze_school(school)

    def _analyze_world_finals(self) -> None:
        print(f'Analyzing Mexico results in the World Finals')
        with MarkdownFile(self._get_filename('mexico.md')) as markdown:
            with markdown.section('Resultados de México en el ICPC'):
                with markdown.section('Final Mundial'):
                    for contest in self.contests:
                        if contest.type != ContestType.WORLD:
                            continue

                        with markdown.section(contest.description()):
                            for team in contest.team_results:
                                if team.country != 'mexico':
                                    continue
                                community_desc = f', {team.community}' if team.community else ''
                                markdown.bullet_point(f'#{team.rank} (#{team.country_rank} de México, '
                                                      f'resolvió {team.problems_solved})'
                                                      f' {team.name} ({team.institution}{community_desc})')

                self._analyze_team_rank(markdown)

    def _analyze_team_rank(self, markdown: Markdown) -> None:
        honorable_teams: List[TeamRank] = []
        high_teams: List[TeamRank] = []
        for contest in self.contests:
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
            markdown.bullet_point(f'{perc}% {team.name} ({team.institution}), resolvió {team.problems_solved} en'
                                  f' {contest.year+1}, obteniendo el lugar #{team.rank}')

        with markdown.section('Ranking de equipos'):
            with markdown.section('Sobresalientes'):
                for team in high_teams:
                    print_team(team)

            with markdown.section('Mención honorífica'):
                for team in honorable_teams:
                    print_team(team)

    def _analyze_community(self, community: SchoolCommunity, community_name: str) -> None:
        print(f'Analyzing results of {community_name}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(community_name)}.md')) as markdown:
            with markdown.section('Resultados del TecNM en el ICPC'):
                with markdown.section('Final Mundial'):
                    wf_tecnm_school_names: Set[str] = set()
                    wf_tecnm_schools: List[School] = []
                    for contest in self.contests:
                        if contest.type != ContestType.WORLD:
                            continue

                        participations = []
                        for team in contest.team_results:
                            if team.community != community:
                                continue
                            participations.append(f'#{team.rank} (#{team.country_rank} de México,'
                                                  f' resolvió {team.problems_solved}) {team.name} ({team.institution})')

                            school = get_school(team.institution, self.schools)
                            if school.name not in wf_tecnm_school_names:
                                wf_tecnm_school_names.add(school.name)
                                wf_tecnm_schools.append(school)

                        if participations:
                            with markdown.section(contest.description()):
                                for participation in participations:
                                    markdown.bullet_point(participation)

                with markdown.section('Top 5 en el regional de México'):
                    for contest in self.contests:
                        if contest.type != ContestType.REGIONAL:
                            continue

                        with markdown.section(contest.description()):
                            for team in contest.team_results:
                                if team.community != SchoolCommunity.TECNM:
                                    continue
                                if team.community_rank > 5:
                                    break
                                markdown.bullet_point(f'#{team.rank} (#{team.community_rank} de TecNM)'
                                                      f' {team.name} ({team.institution})')

    def _analyze_school(self, school: School) -> None:
        with MarkdownFile(self._get_filename('schools', f'{normalize_as_filename(school.name)}.md')) as markdown:
            with markdown.section(school.name.title()):
                contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
                for contest in self.contests:
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

                    with markdown.section(f'{year}-{year+1}'):
                        if best_team:
                            community_rank = ''
                            if best_team.community == SchoolCommunity.TECNM:
                                community_rank = f' (#{best_team.community_rank} de TecNM)'
                            markdown.bullet_point(f'#{best_team.rank}{community_rank} {best_team.name} ({result_type})')
                        if wf_team:
                            markdown.bullet_point(f'Avanzó a la final mundial, donde resolvió '
                                                  f'{wf_team.problems_solved} problemas',
                                                  indent=1)
