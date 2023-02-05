import os
from typing import List, Set, Tuple

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity, School, MEXICO, TeamResult, Contest
from icpc_mexico.markdown import Markdown, MarkdownFile
from icpc_mexico.queries import get_best_by_school, get_by_school, Queries
from icpc_mexico.query_data import RankedTeam
from icpc_mexico.utils import normalize_as_filename, log_run_time, get_percentile, format_percentile

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
                with markdown.section('Final Mundial'):
                    wf_school_names: Set[str] = set()
                    wf_schools: List[School] = []
                    for contest in self._queries.get_contests_by_type(ContestType.WORLD):
                        participations = []
                        for team in contest.team_results:
                            school = self._queries.get_school(team.institution)
                            if school is None or school.state != state:
                                continue
                            participations.append(f'#{team.rank} (#{team.country_rank} de México,'
                                                  f' resolvió {team.problems_solved}) {team.name} ({team.institution})')
                            if school.name not in wf_school_names:
                                wf_school_names.add(school.name)
                                wf_schools.append(school)

                        if participations:
                            with markdown.section(contest.description()):
                                for participation in participations:
                                    markdown.bullet_point(participation)

                with markdown.section('Mejores 5 en México'):
                    # TODO: Get overall rank to take qualifiers into account
                    for contest in self._queries.get_contests_by_type(ContestType.REGIONAL):
                        contest_teams = []
                        rank = 0
                        for team in contest.team_results:
                            school = self._queries.get_school(team.institution)
                            if school is None or school.state != state:
                                continue

                            rank += 1
                            if rank > 5:
                                break
                            contest_teams.append(team)

                        if contest_teams:
                            with markdown.section(contest.description()):
                                for team in contest_teams:
                                    markdown.bullet_point(f'#{team.rank} {team.name} ({team.institution})')

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

                teams: List[Tuple[float, Contest, TeamResult]] = []
                for season in self._queries.contest_seasons:
                    wf_team = get_best_by_school(school, season.world) if season.world else None
                    qualifier_teams = get_by_school(school, season.qualifier) if season.qualifier else []
                    regional_teams = get_by_school(school, season.regional) if season.regional else []

                    all_teams = []
                    if season.qualifier:
                        all_teams.extend(season.qualifier.team_results)
                    if season.regional:
                        all_teams.extend(season.regional.team_results)
                    all_team_names: Set[str] = set()
                    for team in all_teams:
                        all_team_names.add(team.name)

                    if wf_team:
                        team_count = len(season.world.team_results)
                        percentile = get_percentile(wf_team.rank, team_count)
                        teams.append((percentile, season.world, wf_team))

                    added_teams: Set[str] = set()
                    if wf_team:
                        added_teams.add(wf_team.name)

                    teams_with_contest: List[Tuple[TeamResult, Contest]] = []
                    if season.regional:
                        teams_with_contest.extend([(team, season.regional) for team in regional_teams])
                    if season.qualifier:
                        teams_with_contest.extend([(team, season.qualifier) for team in qualifier_teams])
                    for team, contest in teams_with_contest:
                        if team.name in added_teams:
                            continue
                        added_teams.add(team.name)

                        team_count = len(all_team_names)
                        percentile = get_percentile(team.rank, team_count)
                        teams.append((percentile, contest, team))

                def sort_team(team: Tuple[float, Contest, TeamResult]):
                    percentile, contest, team_result = team
                    return (
                        1 if contest.type == ContestType.WORLD else 2,
                        1 - percentile,
                        team_result.problems_solved or 0,
                        team_result.name,
                    )

                teams.sort(key=sort_team)
                with markdown.section('Mejores 10 equipos'):
                    for team in teams[:10]:
                        percentile, contest, team_result = team
                        markdown.numbered_bullet_point(
                            f'_{team_result.name}_: resolvió {team_result.problems_solved} problemas'
                            f' y obtuvo el lugar #{team_result.rank} ({format_percentile(percentile)}) en'
                            f' {contest.name}')

                with markdown.section('Participaciones'):
                    for season in self._queries.contest_seasons:
                        wf_team = get_best_by_school(school, season.world) if season.world else None
                        wf_team_desc = None
                        if wf_team:
                            wf_team_desc = (f'Avanzó a la final mundial, donde resolvió '
                                            f'{wf_team.problems_solved} problemas')

                        # Special case for when we have data from the world finals but not from the regional
                        if wf_team and not season.regional:
                            with markdown.section(season.name):
                                markdown.bullet_point(wf_team.name)
                                markdown.bullet_point(wf_team_desc, indent=1)
                            continue

                        # Rank the teams by phase progress and contest rank (implicitly)
                        regional_teams: List[(TeamResult, str)] = []
                        if season.regional:
                            regional_teams = [(school, 'Regional') for school in get_by_school(school, season.regional)]
                        qualifier_teams: List[(TeamResult, str)] = []
                        if season.qualifier:
                            qualifier_teams = [(school, 'Clasificatorio')
                                               for school in get_by_school(school, season.qualifier)]
                        year_teams = regional_teams + qualifier_teams

                        if not year_teams:
                            # School did not participate this year
                            continue

                        with markdown.section(season.name):
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
