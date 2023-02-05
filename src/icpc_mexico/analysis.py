import os
from typing import List, Set, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import Queries
from icpc_mexico.query_data import RankedTeam, ExtendedTeamResult
from icpc_mexico.utils import normalize_as_filename, log_run_time, format_percentile

TeamRank = Tuple[float, FinishedContest, TeamResult]


class Analyzer:
    def __init__(self, queries: Queries, analysis_path: str):
        self._queries = queries
        self.analysis_path = analysis_path

    def _get_filename(self, *filepath: str) -> str:
        return os.path.join(self.analysis_path, *filepath)

    @log_run_time
    def analyze(self) -> None:
        self._analyze_world_finals()
        self._analyze_community(SchoolCommunity.TECNM, 'TecNM')
        self._analyze_state('sinaloa')

    @log_run_time
    def _analyze_world_finals(self) -> None:
        print(f'Analyzing Mexico results in the World Finals')
        with MarkdownFile(self._get_filename('mexico.md')) as markdown:
            with markdown.section('Resultados de México en el ICPC'):
                with markdown.section('Final Mundial'):
                    for season in self._queries.contest_seasons:
                        contest = season.world
                        if not contest:
                            continue

                        with markdown.section(contest.description()):
                            for team in contest.team_results:
                                if team.country != MEXICO:
                                    continue
                                community_desc = f', {team.community}' if team.community else ''
                                markdown.bullet_point(f'#{team.rank} (#{team.country_rank} de México, '
                                                      f'resolvió {team.problems_solved})'
                                                      f' {team.name} ({team.institution}{community_desc})')

                self._analyze_team_rank(markdown)

    @log_run_time
    def _analyze_team_rank(self, markdown: Markdown) -> None:
        honorable_teams: List[RankedTeam] = []
        high_teams: List[RankedTeam] = []
        for season in self._queries.contest_seasons:
            contest = season.world
            if not contest:
                continue

            last_rank = contest.team_results[-1].rank
            for team in season.teams:
                if not team.school or team.school.country != MEXICO:
                    continue
                ext_result = team.world_result
                if not ext_result or not ext_result.team_result.problems_solved:
                    continue

                if ext_result.team_result.rank == last_rank or ext_result.percentile < 0.5:
                    honorable_teams.append(team)
                else:
                    high_teams.append(team)

        def team_sort(team: RankedTeam) -> Tuple:
            ext_result = team.world_result
            return -ext_result.percentile, -ext_result.team_result.problems_solved, ext_result.contest.year, team.name

        honorable_teams.sort(key=team_sort)
        high_teams.sort(key=team_sort)

        def print_team(team: RankedTeam) -> None:
            ext_result = team.world_result
            markdown.bullet_point(f'{format_percentile(ext_result.percentile)} {team.name}'
                                  f' ({team.school.name.title()}),'
                                  f' resolvió {ext_result.team_result.problems_solved} en {ext_result.contest.year+1},'
                                  f' obteniendo el lugar #{ext_result.team_result.rank}')

        with markdown.section('Ranking de equipos'):
            with markdown.section('Sobresalientes'):
                for team in high_teams:
                    print_team(team)

            with markdown.section('Mención honorífica'):
                for team in honorable_teams:
                    print_team(team)

    @log_run_time
    def _analyze_community(self, community: SchoolCommunity, community_name: str) -> None:
        print(f'Analyzing results of community {community_name}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(community_name)}.md')) as markdown:
            with markdown.section(f'Resultados de {community_name} en el ICPC'):
                with markdown.section('Final Mundial'):
                    wf_school_names: Set[str] = set()
                    wf_schools: List[School] = []
                    for contest in self._queries.get_contests_by_type(ContestType.WORLD):
                        participations = []
                        for team in contest.team_results:
                            if team.community != community:
                                continue
                            participations.append(f'#{team.rank} (#{team.country_rank} de México,'
                                                  f' resolvió {team.problems_solved}) {team.name} ({team.institution})')

                            school = self._queries.get_school(team.institution)
                            if school.name not in wf_school_names:
                                wf_school_names.add(school.name)
                                wf_schools.append(school)

                        if participations:
                            with markdown.section(contest.description()):
                                for participation in participations:
                                    markdown.bullet_point(participation)

                with markdown.section('Mejores 5 en el regional de México'):
                    for contest in self._queries.get_contests_by_type(ContestType.REGIONAL):
                        with markdown.section(contest.description()):
                            for team in contest.team_results:
                                if team.community != community:
                                    continue
                                if team.community_rank > 5:
                                    break
                                markdown.bullet_point(f'#{team.rank} (#{team.community_rank} de {community_name})'
                                                      f' {team.name} ({team.institution})')

    @log_run_time
    def _analyze_state(self, state: str) -> None:
        print(f'Analyzing results of state {state.title()}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(state)}.md')) as markdown:
            with markdown.section(f'Resultados de {state.title()} en el ICPC'):
                teams = self._queries.get_ranked_teams(state=state)
                self._print_ranking(title='Mejores 10 equipos',
                                    teams=teams[:10],
                                    display_school=True,
                                    markdown=markdown)

                with markdown.section('Participaciones'):
                    for season in self._queries.contest_seasons:
                        season_teams = [team for team in season.teams if team.school and team.school.state == state]
                        if not season_teams:
                            # No school from this state participated this year
                            continue

                        with markdown.section(season.name):
                            for team in season_teams:
                                ext_team_result = team.top_result
                                markdown.bullet_point(f'#{ext_team_result.team_result.rank} _{team.name}_'
                                                      f' ({team.school.name.title()})'
                                                      f' ({ext_team_result.contest.type.title()})')

    def analyze_schools_by_country(self, country: str) -> None:
        schools = self._queries.get_schools_by_country(country)
        print(f'Analyzing {len(schools)} schools from {country.title()}')
        for school in schools:
            self._analyze_school(school)

    def _analyze_school(self, school: School) -> None:
        with MarkdownFile(self._get_filename('schools', f'{normalize_as_filename(school.name)}.md')) as markdown:
            with markdown.section(school.name.title()):
                if school.country == MEXICO:
                    markdown.paragraph(':warning: Equipos que solo participaron en el Repechaje del '
                                       'Gran Premio de México no están registrados oficialmente en el ICPC, '
                                       'por lo que no aparecerán aquí.')

                teams = self._queries.get_ranked_teams(school=school)
                self._print_ranking(title='Mejores 10 equipos',
                                    teams=teams[:10],
                                    display_school=False,
                                    markdown=markdown)

                with markdown.section('Participaciones'):
                    for season in self._queries.contest_seasons:
                        season_teams = [team for team in season.teams if team.school == school]
                        if not season_teams:
                            # School did not participate this year
                            continue

                        with markdown.section(season.name):
                            for team in season_teams:
                                ext_team_result = team.top_result
                                community_rank = ''
                                if team.school.community == SchoolCommunity.TECNM:
                                    community_rank = f' (#{ext_team_result.team_result.community_rank} de TecNM)'
                                markdown.bullet_point(f'#{ext_team_result.team_result.rank}{community_rank}'
                                                      f' _{team.name}_'
                                                      f' ({ext_team_result.contest.type.title()})')

    def _print_ranking(self, title: str, teams: List[RankedTeam], display_school: bool, markdown: Markdown) -> None:
        def result_to_str(result: ExtendedTeamResult, percentile: float) -> str:
            return (f'resolvió {result.team_result.problems_solved} problemas'
                    f' y obtuvo el lugar #{result.team_result.rank}'
                    f' ({format_percentile(percentile)}) en'
                    f' {result.contest.name}')

        with markdown.section(title):
            for team in teams[:10]:
                school_str = f' ({team.school.name.title()})' if display_school else ''
                top_result = team.regional_result or team.qualifier_result
                if top_result:
                    markdown.numbered_bullet_point(
                        f'_{team.name}_{school_str} {result_to_str(top_result, team.regional_season_percentile)}')
                    world_result = team.world_result
                    if world_result:
                        markdown.bullet_point(
                            (f'Avanzó a la final mundial y'
                             f' {result_to_str(world_result, world_result.percentile)}'),
                            indent=1)
                else:
                    top_result = team.world_result
                    markdown.numbered_bullet_point(
                        f'_{team.name}_{school_str} {result_to_str(top_result, top_result.percentile)}')
                    markdown.bullet_point('No hay datos del regional', indent=1)
