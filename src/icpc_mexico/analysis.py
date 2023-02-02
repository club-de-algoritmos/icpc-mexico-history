import os
from collections import defaultdict
from typing import List, Dict, Set, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult, Contest
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import get_by_type, get_best_by_school, get_school, get_by_school
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
                if school.country == MEXICO:
                    markdown.paragraph(':warning: Equipos que solo participaron en el Repechaje del '
                                       'Gran Premio de México no están registrados oficialmente en el ICPC, '
                                       'por lo que no aparecerán aquí.')

                contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
                for contest in self.contests:
                    contests_by_year[contest.year].append(contest)

                teams: List[Tuple[float, Contest, TeamResult]] = []
                for year, contests in contests_by_year.items():
                    regional = get_by_type(ContestType.REGIONAL, contests)
                    world = get_by_type(ContestType.WORLD, contests)
                    wf_team = get_best_by_school(school, world) if world else None
                    regional_teams: List[TeamResult] = []
                    if regional:
                        regional_teams = get_by_school(school, regional)

                    if wf_team:
                        team_count = len(world.team_results)
                        percentile = (team_count - wf_team.rank) / (team_count - 1)
                        teams.append((1 - percentile, world, wf_team))

                    for team in regional_teams:
                        if wf_team and wf_team.name == team.name:
                            continue
                        teams.append((team.rank, regional, team))

                # TODO: Sort by regional percentile instead of rank (need to make the union out of the qualifier
                #  and the regional teams to get a proper count, taking repechaje into account)
                def sort_team(team: Tuple[float, Contest, TeamResult]):
                    rank_or_percentile, contest, team_result = team
                    return (
                        1 if contest.type == ContestType.WORLD else 2,
                        rank_or_percentile,
                        team_result.problems_solved,
                        team_result.name,
                    )

                teams.sort(key=sort_team)
                with markdown.section('Top 10 equipos'):
                    for team in teams[:10]:
                        _, contest, team_result = team
                        markdown.bullet_point(
                            f'#{team_result.rank} {team_result.name}, resolvió {team_result.problems_solved} problemas'
                            f' en {contest.name}')

                with markdown.section('Participaciones'):
                    for year, contests in contests_by_year.items():
                        regional = get_by_type(ContestType.REGIONAL, contests)
                        qualifier = (get_by_type(ContestType.GRAN_PREMIO, contests) or
                                     get_by_type(ContestType.PROGRAMMING_BATTLE, contests))
                        world = get_by_type(ContestType.WORLD, contests)
                        wf_team = get_best_by_school(school, world) if world else None

                        section_title = f'{year}-{year + 1}'
                        wf_team_desc = None
                        if wf_team:
                            wf_team_desc = (f'Avanzó a la final mundial, donde resolvió '
                                            f'{wf_team.problems_solved} problemas')

                        # Special case for when we have data from the world finals but not from the regional
                        if wf_team and not regional:
                            with markdown.section(section_title):
                                markdown.bullet_point(wf_team.name)
                                markdown.bullet_point(wf_team_desc, indent=1)
                            continue

                        # Rank the teams by phase progress and contest rank (implicitly)
                        regional_teams: List[(TeamResult, str)] = []
                        if regional:
                            regional_teams = [(school, 'Regional') for school in get_by_school(school, regional)]
                        qualifier_teams: List[(TeamResult, str)] = []
                        if qualifier:
                            qualifier_teams = [(school, 'Clasificatorio') for school in get_by_school(school, qualifier)]
                        year_teams = regional_teams + qualifier_teams

                        if not year_teams:
                            # School did not participate this year
                            continue

                        with markdown.section(section_title):
                            # Only show the top appearance of every team
                            seen_teams: Set[str] = set()
                            for team, contest_type in year_teams:
                                if team.name in seen_teams:
                                    continue
                                seen_teams.add(team.name)

                                community_rank = ''
                                if team.community == SchoolCommunity.TECNM:
                                    community_rank = f' (#{team.community_rank} de TecNM)'
                                markdown.bullet_point(f'#{team.rank}{community_rank} {team.name} ({contest_type})')
                                if wf_team and wf_team.name == team.name:
                                    markdown.bullet_point(wf_team_desc, indent=1)
