import os
from collections import defaultdict
from typing import List, Set, Tuple, Dict

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import Queries
from icpc_mexico.query_data import RankedTeam, ExtendedTeamResult, ContestSeason
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
                        for contest in season.worlds:
                            with markdown.section(contest.description()):
                                for team in contest.team_results:
                                    if team.country != MEXICO:
                                        continue
                                    community_desc = f', {team.community}' if team.community else ''
                                    markdown.bullet_point(f'#{team.rank} (#{team.country_rank} de México, '
                                                          f'resolvió {team.problems_solved})'
                                                          f' {team.name} ({team.institution}{community_desc})')

                high_teams: List[RankedTeam] = []
                teams = self._queries.get_ranked_teams(country=MEXICO)
                for team in teams:
                    ext_result = team.world_result
                    if not ext_result or not ext_result.team_result.problems_solved:
                        continue

                    # Check whether the team was in the top half of the ranking
                    last_rank = ext_result.contest.team_results[-1].rank
                    if ext_result.team_result.rank < last_rank and ext_result.percentile >= 0.5:
                        high_teams.append(team)

                self._print_detailed_ranking(title='Equipos sobresalientes',
                                             teams=high_teams,
                                             markdown=markdown,
                                             display_world_only=True)

            with markdown.section('Ranking de escuelas'):
                recent_seasons = []
                world_finals_count = 0
                for season in reversed(self._queries.contest_seasons):
                    recent_seasons.append(season)
                    if season.worlds:
                        world_finals_count += 1
                        if world_finals_count == 5:
                            break

                self._print_school_ranking(markdown, 'Últimos 5 años', recent_seasons)
                self._print_school_ranking(markdown, 'Histórico', self._queries.contest_seasons)

    def _print_school_ranking(self, markdown: Markdown, title: str, seasons: List[ContestSeason]) -> None:
        school_stats: Dict[str, List] = defaultdict(lambda: [0, 0, 0])
        for season in seasons:
            for team in season.teams:
                if not team.school or team.school.country != MEXICO:
                    continue

                stat = school_stats[team.school.name.title()]
                if team.world_result:
                    stat[0] += 1
                elif team.regional_result:
                    stat[1] += 1
                elif team.qualifier_result:
                    stat[2] += 1

        school_ranking = sorted(school_stats.items(), key=lambda school_stat: school_stat[1], reverse=True)
        rank = 0
        school_table = []
        for school, stats in school_ranking:
            if stats[0]:  # Only world finalist schools
                rank += 1
                school_table.append([str(rank), school] + list(map(str, stats)))
        with markdown.section(title):
            markdown.table(['#', 'Escuela', 'Finales mundiales', 'Regionales', 'Clasificatorios'], school_table)

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
                    for season in self._queries.contest_seasons:
                        season_teams = [team
                                        for team in season.teams
                                        if team.school and
                                        team.school.community == community and
                                        team.regional_result and
                                        team.regional_result.team_result.community_rank <= 5 and
                                        team.regional_result.team_result.problems_solved]
                        self._print_simple_ranking(season.name, season_teams, markdown)

    @log_run_time
    def _analyze_state(self, state: str) -> None:
        print(f'Analyzing results of state {state.title()}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(state)}.md')) as markdown:
            with markdown.section(f'Resultados de {state.title()} en el ICPC'):
                teams = self._queries.get_ranked_teams(state=state)
                self._print_detailed_ranking(title='Mejores 10 equipos', teams=teams[:10], markdown=markdown)

                with markdown.section('Participaciones'):
                    for season in self._queries.contest_seasons:
                        season_teams = [team for team in season.teams if team.school and team.school.state == state]
                        self._print_simple_ranking(season.name, season_teams, markdown)

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
                self._print_detailed_ranking(title='Mejores 10 equipos',
                                             teams=teams[:10],
                                             markdown=markdown,
                                             display_school=False)

                with markdown.section('Participaciones'):
                    for season in self._queries.contest_seasons:
                        season_teams = [team for team in season.teams if team.school == school]
                        self._print_simple_ranking(season.name, season_teams, markdown, display_school=False)

    def _print_detailed_ranking(self,
                                title: str,
                                teams: List[RankedTeam],
                                markdown: Markdown,
                                display_school: bool = True,
                                display_world_only: bool = False,
                                ) -> None:
        if not teams:
            return

        def result_to_str(result: ExtendedTeamResult, percentile: float) -> str:
            return (f'resolvió {result.team_result.problems_solved} problemas'
                    f' y obtuvo el lugar #{result.team_result.rank}'
                    f' ({format_percentile(percentile)}) en'
                    f' {result.contest.name}')

        with markdown.section(title):
            for team in teams:
                school_str = f' ({team.school.name.title()})' if display_school else ''
                top_result = team.regional_result or team.qualifier_result
                if top_result and not display_world_only:
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
                    if not display_world_only:
                        markdown.bullet_point('No hay datos del regional', indent=1)

    def _print_simple_ranking(self,
                              title: str,
                              teams: List[RankedTeam],
                              markdown: Markdown,
                              display_school: bool = True,
                              ) -> None:
        if not teams:
            return

        with markdown.section(title):
            for team in teams:
                school_str = f' ({team.school.name.title()})' if display_school else ''
                top_result = team.regional_result or team.qualifier_result
                community_rank = ''
                if team.school.community == SchoolCommunity.TECNM:
                    community_rank = f' (#{top_result.team_result.community_rank} de TecNM)'
                markdown.numbered_bullet_point(f'#{top_result.team_result.rank}{community_rank}'
                                               f' _{team.name}_{school_str}'
                                               f' ({top_result.contest.type.title()})')
                world_result = team.world_result
                if world_result:
                    markdown.bullet_point(
                        (f'Avanzó a la final mundial y resolvió {world_result.team_result.problems_solved}'
                         f' problemas obtuviendo el lugar #{world_result.team_result.rank}'
                         f' ({format_percentile(world_result.percentile)}) en'
                         f' {world_result.contest.name}'),
                        indent=1)
