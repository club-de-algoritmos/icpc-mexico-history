import dataclasses
from collections import defaultdict
from typing import List, Optional, Dict, Tuple

from icpc_mexico.data import School, ContestType, FinishedContest, TeamResult, SchoolCommunity, Contest
from icpc_mexico.query_data import ContestSeason, RankedTeam, ExtendedTeamResult
from icpc_mexico.utils import normalize_str, get_percentile


def get_school(school_name: str, schools: List[School]) -> Optional[School]:
    school_name = normalize_str(school_name)
    for school in schools:
        if school.matches_name(school_name):
            return school
    return None


def get_by_type(contest_type: ContestType, contests: List[FinishedContest]) -> Optional[FinishedContest]:
    for contest in contests:
        if contest.type == contest_type:
            return contest
    return None


def get_by_school(school: School, contest: FinishedContest) -> List[TeamResult]:
    return [team for team in contest.team_results if school.matches_name(team.institution)]


def get_best_by_school(school: School, contest: FinishedContest) -> Optional[TeamResult]:
    teams = get_by_school(school, contest)
    if teams:
        return teams[0]
    return None


def _sort_ranked_team(team: RankedTeam) -> Tuple:
    world_finals_percentile = -1
    if team.world_result:
        world_finals_percentile = team.world_result.percentile

    problems_solved = team.top_result.team_result.problems_solved or 0
    rank = team.top_result.team_result.rank or 1000

    return (-world_finals_percentile,
            -round((team.regional_season_percentile or -1) * 100),
            rank,
            -problems_solved,
            team.name)


class Queries:
    def __init__(self, contests: List[FinishedContest], schools: List[School]):
        self._schools = schools

        self._schools_by_name: Dict[str, School] = {}
        for school in self._schools:
            for name in school.get_all_matching_names():
                self._schools_by_name[name] = school

        self._contests = self._compute_extra_team_results(contests)

    def _compute_extra_team_results(self, contests: List[FinishedContest]) -> List[FinishedContest]:
        computed_contests = []
        for contest in contests:
            community_last_team: Dict[SchoolCommunity, TeamResult] = {}
            community_rank: Dict[SchoolCommunity, int] = defaultdict(int)
            country_last_team: Dict[str, TeamResult] = {}
            country_rank: Dict[str, int] = defaultdict(int)
            # TODO: Compute
            # super_region_ranking: Dict[SuperRegion, int] = defaultdict(int)
            team_results = []
            for team in contest.team_results:
                school = self.get_school(team.institution)

                if school is None:
                    # We're only interested in Mexico, do a simple check just in case
                    if contest.type in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
                        if team.site_citation != 'Invitado':
                            raise ValueError(f'Unexpected team without a school: '
                                             f'team {team.name} with school {team.institution}')
                        continue

                    team_results.append(team)
                    continue

                if school.community:
                    community_rank[school.community] += 1
                    rank = community_rank[school.community]
                    last_team = community_last_team.get(school.community)
                    if last_team and last_team.rank == team.rank:
                        rank = last_team.community_rank

                    team = dataclasses.replace(team,
                                               community=school.community,
                                               community_rank=rank)
                    community_last_team[school.community] = team

                if contest.type == ContestType.WORLD:
                    country_rank[school.country] += 1
                    rank = country_rank[school.country]
                    last_team = country_last_team.get(school.country)
                    if last_team and last_team.rank == team.rank:
                        rank = last_team.country_rank

                    team = dataclasses.replace(team,
                                               country=school.country,
                                               country_rank=rank)
                    country_last_team[school.country] = team

                team_results.append(team)

            computed_contests.append(dataclasses.replace(contest, team_results=team_results))

        return computed_contests

    @property
    def contest_seasons(self) -> List[ContestSeason]:
        seasons: List[ContestSeason] = []
        contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
        for contest in self._contests:
            contests_by_year[contest.year].append(contest)

        for year, contests in contests_by_year.items():
            qualifier = None
            regional = None
            world = None
            for contest in contests:
                if contest.type in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
                    qualifier = contest
                elif contest.type == ContestType.REGIONAL:
                    regional = contest
                elif contest.type == ContestType.WORLD:
                    world = contest
                else:
                    raise ValueError(f'Unexpected type {contest.type} of contest {contest.name}')

            results_by_team_name: Dict[str, List[Optional[ExtendedTeamResult]]] = defaultdict(lambda: 3 * [None])
            for i, contest in enumerate([world, regional, qualifier]):
                if not contest:
                    continue
                for team_result in contest.team_results:
                    results_by_team_name[team_result.name][i] = ExtendedTeamResult(
                        team_result=team_result, contest=contest)

            regional_teams = {result.name for result in regional.team_results} if regional else set()
            qualifier_teams = {result.name for result in qualifier.team_results} if qualifier else set()
            extra_teams_in_regional = regional_teams - qualifier_teams
            regional_season_teams = regional_teams | qualifier_teams

            teams: List[RankedTeam] = []
            for team_name, ext_team_results in results_by_team_name.items():
                school_names = [result.team_result.institution for result in ext_team_results if result]
                school = self.get_school(school_names[0])
                world_result, regional_result, qualifier_result = ext_team_results

                regional_season_rank = None
                if regional_result:
                    regional_season_rank = regional_result.team_result.rank
                elif qualifier_result:
                    # Teams that were in the regional but were not in the qualifiers, will push down teams that did not
                    # make it to the regional
                    regional_season_rank = qualifier_result.team_result.rank + len(extra_teams_in_regional)

                regional_season_percentile = None
                if regional_season_rank:
                    regional_season_percentile = get_percentile(regional_season_rank, len(regional_season_teams))

                teams.append(RankedTeam(name=team_name,
                                        school=school,
                                        qualifier_result=qualifier_result,
                                        regional_result=regional_result,
                                        world_result=world_result,
                                        regional_season_rank=regional_season_rank,
                                        regional_season_percentile=regional_season_percentile))

            teams.sort(key=_sort_ranked_team)

            seasons.append(ContestSeason(year=year, qualifier=qualifier, regional=regional, world=world, teams=teams))

        return seasons

    def get_contests_by_type(self, contest_type: ContestType) -> List[Contest]:
        return [contest for contest in self._contests if contest.type == contest_type]

    def get_school(self, name: str) -> Optional[School]:
        return self._schools_by_name.get(normalize_str(name))

    def get_schools_by_country(self, country: str) -> List[School]:
        return [school for school in self._schools if school.country == country]

    def get_ranked_teams(self, country: Optional[str] = None,
                         state: Optional[str] = None,
                         school: Optional[School] = None,
                         ) -> List[RankedTeam]:
        teams: List[RankedTeam] = []
        for season in self.contest_seasons:
            for team in season.teams:
                if country and (not team.school or team.school.country != country):
                    continue
                if state and (not team.school or team.school.state != state):
                    continue
                if school and school != team.school:
                    continue
                teams.append(team)
        return sorted(teams, key=_sort_ranked_team)
