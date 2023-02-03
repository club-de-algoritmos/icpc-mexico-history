import dataclasses
from collections import defaultdict
from typing import List, Optional, Dict

from icpc_mexico.data import School, ContestType, FinishedContest, TeamResult, SchoolCommunity, Contest
from icpc_mexico.query_data import ContestSeason
from icpc_mexico.utils import normalize_str


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

            seasons.append(ContestSeason(year=year, qualifier=qualifier, regional=regional, world=world))

        return seasons

    def get_contests_by_type(self, contest_type: ContestType) -> List[Contest]:
        return [contest for contest in self._contests if contest.type == contest_type]

    def get_school(self, name: str) -> Optional[School]:
        return self._schools_by_name.get(normalize_str(name))

    def get_schools_by_country(self, country: str) -> List[School]:
        return [school for school in self._schools if school.country == country]
