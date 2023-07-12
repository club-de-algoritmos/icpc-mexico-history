import os
import shutil
from collections import defaultdict
from typing import List, Set, Tuple, Dict, Optional

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import Queries
from icpc_mexico.query_data import RankedTeam, ExtendedTeamResult, ContestSeason
from icpc_mexico.utils import normalize_as_filename, log_run_time, format_percentile

TeamRank = Tuple[float, FinishedContest, TeamResult]


def _is_mexican_and_eligible(school: Optional[School]) -> bool:
    return school and school.country == MEXICO and school.is_eligible


def _get_school_link(school: School, relative_path: str = '') -> str:
    return f'[{school.name}]({relative_path}{school.slug_name})'


class Analyzer:
    def __init__(self, queries: Queries, analysis_path: str):
        self._queries = queries
        self._analysis_path = analysis_path

    def _get_filename(self, *filepath: str) -> str:
        return os.path.join(self._analysis_path, *filepath)

    @log_run_time
    def analyze(self) -> None:
        self._analyze_world_finals()
        self._analyze_community(SchoolCommunity.TECNM)
        self._analyze_state('sinaloa')

    @log_run_time
    def _analyze_world_finals(self) -> None:
        print(f'Analyzing Mexico results in the World Finals')
        with MarkdownFile(self._get_filename('mexico.md')) as markdown:
            with markdown.section('Resultados de México en el ICPC'):
                with markdown.section('Finales Mundiales'):
                    for season in self._queries.contest_seasons:
                        if not season.worlds:
                            continue
                        with markdown.section(season.name):
                            for contest in season.worlds:
                                markdown.paragraph(contest.name)
                                for team in contest.team_results:
                                    if not _is_mexican_and_eligible(team.school):
                                        continue

                                    solved_str = ''
                                    if team.problems_solved is not None:
                                        solved_str = f', resolvió {team.problems_solved}'
                                    school_link = _get_school_link(team.school, relative_path='escuela/')
                                    markdown.bullet_point(f'#{team.rank} (#{team.country_rank} de México{solved_str})'
                                                          f' {team.name} ({school_link}')

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

                self._print_participation_stats(markdown)

                self._print_school_rankings(markdown)

    def _print_participation_stats(self,
                                   markdown: Markdown,
                                   title: str = 'Participaciones',
                                   community: Optional[SchoolCommunity] = None,
                                   state: Optional[str] = None,
                                   school: Optional[School] = None,
                                   skip_empty: bool = False,
                                   ) -> None:
        participations_table = []
        totals = [0, 0, 0, 0, 0]
        all_schools: Set[str] = set()
        started_participating = False
        for season in self._queries.contest_seasons:
            stats = [0, 0, 0, 0, 0]
            season_schools: Set[str] = set()
            for team in season.teams:
                if not _is_mexican_and_eligible(team.school):
                    continue
                if community and community != team.school.community:
                    continue
                if state and state != team.school.state:
                    continue
                if school and school != team.school:
                    continue

                if team.world_result:
                    stats[0] += 1
                if team.regional_result:
                    stats[1] += 1
                if team.qualifier_result:
                    stats[2] += 1
                stats[3] += 1
                season_schools.add(team.school.name)
                all_schools.add(team.school.name)

            stats[4] = len(season_schools)

            if (skip_empty or not started_participating) and sum(stats) == 0:
                continue
            started_participating = True

            for i in range(len(totals)):
                totals[i] += stats[i]

            participations_table.append([season.name] + list(map(str, stats)))

        totals[4] = len(all_schools)
        participations_table.insert(0, ['**Total**'] + [f'**{total}**' for total in totals])

        headers = ['Temporada', 'Finales mundiales', 'Regionales', 'Clasificatorios', 'Equipos', 'Escuelas']
        if school:
            # Drop the school counts because there is only one school
            headers.pop()
            for participation in participations_table:
                participation.pop()

        with markdown.section(title):
            markdown.table(headers, participations_table)

    def _print_school_rankings(self,
                               markdown: Markdown,
                               community: Optional[SchoolCommunity] = None,
                               state: Optional[str] = None,
                               contest_type: Optional[ContestType] = ContestType.WORLD,
                               ) -> None:
        with markdown.section('Ranking de escuelas'):
            recent_seasons = []
            world_finals_count = 0
            for season in reversed(self._queries.contest_seasons):
                recent_seasons.append(season)
                if season.worlds:
                    world_finals_count += 1
                    if world_finals_count == 5:
                        break

            self._print_school_ranking(
                markdown, 'Últimos 5 años', recent_seasons, community, state, contest_type)
            self._print_school_ranking(
                markdown, 'Histórico', self._queries.contest_seasons, community, state, contest_type)

    def _print_school_ranking(self,
                              markdown: Markdown,
                              title: str,
                              seasons: List[ContestSeason],
                              community: Optional[SchoolCommunity],
                              state: Optional[str],
                              contest_type: Optional[ContestType],
                              ) -> None:
        school_stats: Dict[str, List] = defaultdict(lambda: [0, 0, 0, 0])
        schools_by_name: Dict[str, School] = {}
        for season in seasons:
            for team in season.teams:
                if not _is_mexican_and_eligible(team.school):
                    continue
                if community and community != team.school.community:
                    continue
                if state and state != team.school.state:
                    continue

                schools_by_name[team.school.name] = team.school
                stat = school_stats[team.school.name]
                if team.world_result:
                    stat[0] += 1
                if team.regional_result:
                    stat[1] += 1
                if team.qualifier_result:
                    stat[2] += 1
                stat[3] += 1

        school_ranking = sorted(school_stats.items(),
                                key=lambda school_stat: school_stat[1] + [school_stat[0]],
                                reverse=True)
        rank = 0
        school_table = []
        for school_name, stats in school_ranking:
            if contest_type == ContestType.WORLD and not stats[0]:
                continue
            if contest_type == ContestType.REGIONAL and not (stats[0] + stats[1]):
                continue

            rank += 1
            school_link = _get_school_link(schools_by_name[school_name], relative_path='escuela/')
            school_table.append([str(rank), school_link] + list(map(str, stats)))

        with markdown.section(title):
            markdown.table(['#', 'Escuela', 'Finales mundiales', 'Regionales', 'Clasificatorios', 'Total'],
                           school_table)

    @log_run_time
    def _analyze_community(self, community: SchoolCommunity) -> None:
        print(f'Analyzing results of community {community}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(community.abbreviation)}.md')) as markdown:
            with markdown.section(f'Resultados de {community.abbreviation} en el ICPC'):
                with markdown.section('Finales Mundiales'):
                    wf_school_names: Set[str] = set()
                    wf_schools: List[School] = []
                    for contest in self._queries.get_contests_by_type(ContestType.WORLD):
                        participations = []
                        for team in contest.team_results:
                            if not team.school or team.school.community != community:
                                continue

                            solved_str = ''
                            if team.problems_solved is not None:
                                solved_str = f', resolvió {team.problems_solved}'
                            participations.append(f'#{team.rank} (#{team.country_rank} de México{solved_str})'
                                                  f' {team.name} ({team.school.name})')

                            if team.school.name not in wf_school_names:
                                wf_school_names.add(team.school.name)
                                wf_schools.append(team.school)

                        if participations:
                            with markdown.section(contest.season):
                                markdown.paragraph(contest.name)
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
                        self._print_simple_ranking(season.name, season_teams, markdown, display_community=False)

            self._print_participation_stats(markdown, community=SchoolCommunity.TECNM)

            self._print_school_rankings(markdown, community=SchoolCommunity.TECNM, contest_type=ContestType.REGIONAL)

    @log_run_time
    def _analyze_state(self, state: str) -> None:
        print(f'Analyzing results of state {state.title()}')
        with MarkdownFile(self._get_filename(f'{normalize_as_filename(state)}.md')) as markdown:
            with markdown.section(f'Resultados de {state.title()} en el ICPC'):
                teams = self._queries.get_ranked_teams(state=state)
                self._print_detailed_ranking(title='Mejores 10 equipos', teams=teams[:10], markdown=markdown)

                with markdown.section('Participaciones'):
                    self._print_participation_stats(markdown, title='Resumen', state=state)

                    for season in self._queries.contest_seasons:
                        season_teams = [team for team in season.teams if team.school and team.school.state == state]
                        self._print_simple_ranking(season.name, season_teams, markdown)

                self._print_school_rankings(markdown, state=state, contest_type=None)

    def analyze_schools_by_country(self, country: str) -> None:
        # Re-create the whole school directory so no longer qualifying schools can be dropped
        school_dir = self._get_filename('escuela')
        shutil.rmtree(school_dir, ignore_errors=True)
        os.mkdir(school_dir)

        schools = self._queries.get_schools_by_country(country)
        print(f'Analyzing {len(schools)} schools from {country.title()}')
        for school in schools:
            self._analyze_school(school)

    def _analyze_school(self, school: School) -> None:
        filename = f'{school.slug_name}.md'
        with MarkdownFile(self._get_filename('escuela', filename)) as markdown:
            with markdown.section(school.name):
                teams = self._queries.get_ranked_teams(school=school)
                self._print_detailed_ranking(title='Mejores 10 equipos',
                                             teams=teams[:10],
                                             markdown=markdown,
                                             display_school=False)

                with markdown.section('Participaciones'):
                    self._print_participation_stats(markdown, title='Resumen', school=school, skip_empty=True)

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
            percentile_str = ''
            if percentile >= 0:
                percentile_str = f' ({format_percentile(percentile)})'

            solved_str = ''
            if result.team_result.problems_solved is not None:
                solved_str = f'resolvió {result.team_result.problems_solved} problemas y '
            return (f'{solved_str}obtuvo el lugar #{result.team_result.rank}{percentile_str}'
                    f' en {result.contest.name}')

        with markdown.section(title):
            for team in teams:
                school_link = _get_school_link(team.school, relative_path='escuela/')
                school_str = f' ({school_link})' if display_school else ''
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
                              display_community: bool = True,
                              ) -> None:
        if not teams:
            return

        with markdown.section(title):
            for team in teams:
                school_link = _get_school_link(team.school, relative_path='escuela/')
                school_str = f' ({school_link})' if display_school else ''
                regional_result = team.regional_result or team.qualifier_result
                if regional_result:
                    community_rank = ''
                    if display_community and team.school.community:
                        community_rank = (f' (#{regional_result.team_result.community_rank}'
                                          f' de {team.school.community.abbreviation})')
                    markdown.numbered_bullet_point(f'#{regional_result.team_result.rank}{community_rank}'
                                                   f' _{team.name}_{school_str}'
                                                   f' ({regional_result.contest.type.title()})')
                else:
                    markdown.numbered_bullet_point('No hay datos del regional')

                world_result = team.world_result
                if world_result:
                    percentile_str = ''
                    if world_result.percentile >= 0:
                        percentile_str = f' ({format_percentile(world_result.percentile)})'
                    solved_str = ''
                    if world_result.team_result.problems_solved is not None:
                        solved_str = f' y resolvió {world_result.team_result.problems_solved} problemas'
                    markdown.bullet_point(
                        (f'Avanzó a la final mundial{solved_str} obtuviendo el lugar #{world_result.team_result.rank}{percentile_str}'
                         f' en {world_result.contest.name}'),
                        indent=1)
