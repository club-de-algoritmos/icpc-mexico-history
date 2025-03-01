import dataclasses
import math
from collections import defaultdict
from typing import List, Optional, Dict, Tuple

from icpc_mexico.data import School, ContestType, FinishedContest, TeamResult, SchoolCommunity, Contest
from icpc_mexico.query_data import ContestSeason, RankedTeam, ExtendedTeamResult
from icpc_mexico.utils import get_percentile, normalize_school_name


def get_school(school_name: str, schools: List[School]) -> Optional[School]:
    for school in schools:
        if school.matches_name(school_name):
            return school
    return None


def get_by_type(contest_type: ContestType, contests: List[FinishedContest]) -> Optional[FinishedContest]:
    for contest in contests:
        if contest.type == contest_type:
            return contest
    return None


def _sort_ranked_team(team: RankedTeam) -> Tuple:
    world_finals_percentile = -1
    if team.world_result:
        world_finals_percentile = team.world_result.percentile

    championship_percentile = -1
    if team.championship_result:
        championship_percentile = team.championship_result.percentile

    problems_solved = team.top_result.team_result.problems_solved or 0
    rank = team.top_result.team_result.rank or 1000

    return (-world_finals_percentile,
            -championship_percentile,
            -round((team.regional_season_percentile or -1) * 100),
            rank,
            -problems_solved,
            team.name)


class Queries:
    def __init__(self, contests: List[FinishedContest], schools: List[School]):
        self._schools = schools

        self._schools_by_name: Dict[str, School] = {}
        for school in self._schools:
            for name in school.names:
                self._schools_by_name[name] = school

        self._contests = self._compute_extra_team_results(contests)

    def _compute_extra_team_results(self, contests: List[FinishedContest]) -> List[FinishedContest]:
        computed_contests = []
        for contest in contests:
            community_last_team: Dict[SchoolCommunity, TeamResult] = {}
            community_rank: Dict[SchoolCommunity, int] = defaultdict(int)
            championship_country_last_team: Dict[str, TeamResult] = {}
            championship_country_rank: Dict[str, int] = defaultdict(int)
            wf_country_last_team: Dict[str, TeamResult] = {}
            wf_country_rank: Dict[str, int] = defaultdict(int)
            team_results = []
            for team in contest.team_results:
                school = self._get_school(team.institution)
                if school is None:
                    # We're only interested in Mexico, do a simple check just in case
                    if contest.type in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
                        if team.site_citation != 'Invitado':
                            raise ValueError(f'Unexpected team without a school: '
                                             f'team {team.name} with school {team.institution}')
                        continue

                    team_results.append(team)
                    continue

                team = dataclasses.replace(team, school=school)

                if school.community:
                    community_rank[school.community] += 1
                    rank = community_rank[school.community]
                    last_team = community_last_team.get(school.community)
                    if last_team and last_team.rank == team.rank:
                        rank = last_team.community_rank

                    team = dataclasses.replace(team, community_rank=rank)
                    community_last_team[school.community] = team

                if contest.type == ContestType.CHAMPIONSHIP:
                    championship_country_rank[school.country] += 1
                    rank = championship_country_rank[school.country]
                    last_team = championship_country_last_team.get(school.country)
                    if last_team and last_team.rank == team.rank:
                        rank = last_team.championship_country_rank

                    team = dataclasses.replace(team, championship_country_rank=rank)
                    championship_country_last_team[school.country] = team

                if contest.type == ContestType.WORLD:
                    wf_country_rank[school.country] += 1
                    rank = wf_country_rank[school.country]
                    last_team = wf_country_last_team.get(school.country)
                    if last_team and last_team.rank == team.rank:
                        rank = last_team.country_rank

                    team = dataclasses.replace(team, country_rank=rank)
                    wf_country_last_team[school.country] = team

                team_results.append(team)

            computed_contests.append(dataclasses.replace(contest, team_results=team_results))

        return computed_contests

    @property
    def contest_seasons(self) -> List[ContestSeason]:
        seasons: List[ContestSeason] = []
        contests_by_year: Dict[int, List[FinishedContest]] = defaultdict(list)
        for contest in self._contests:
            contests_by_year[contest.year].append(contest)

        for year, contests in sorted(contests_by_year.items()):
            qualifier = None
            regional = None
            championship = None
            worlds = []
            for contest in contests:
                if contest.type in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
                    if qualifier is not None:
                        raise Exception(f'Found two contests with the same type ({contest.type}):'
                                        f' {qualifier} and {contest}')
                    qualifier = contest
                elif contest.type == ContestType.REGIONAL:
                    if regional is not None:
                        raise Exception(f'Found two contests with the same type ({contest.type}):'
                                        f' {regional} and {contest}')
                    regional = contest
                elif contest.type == ContestType.CHAMPIONSHIP:
                    if championship is not None:
                        raise Exception(f'Found two contests with the same type ({contest.type}):'
                                        f' {championship} and {contest}')
                    championship = contest
                elif contest.type == ContestType.WORLD:
                    worlds.append(contest)
                else:
                    raise ValueError(f'Unexpected type {contest.type} of contest {contest.name}')

            # TODO: Create a SeasonTeamResult dataclass
            results_by_team_name: Dict[str, List[Optional[ExtendedTeamResult]]] = defaultdict(lambda: 4 * [None])
            # Process world contests at the end to properly match with the regionals when a team name change occurs
            for contest in ([championship, regional, qualifier] + worlds):
                if not contest:
                    continue
                if contest in worlds:
                    contest_index = 0
                elif contest == championship:
                    contest_index = 1
                elif contest == regional:
                    contest_index = 2
                elif contest == qualifier:
                    contest_index = 3
                else:
                    raise Exception(f'Unexpected contest {contest}')

                for team_result in contest.team_results:
                    team_name = team_result.name
                    if contest_index == 0 and not results_by_team_name[team_name][2]:
                        # Detect teams that change their name going into the World Finals, keeping the regional name as
                        # Mexico got to know them, because team names are not important in the World Finals
                        old_team_name = None
                        old_team_rank = math.inf
                        for other_team_name, other_team_results in results_by_team_name.items():
                            other_team_result = other_team_results[2].team_result if other_team_results[2] else None
                            if (other_team_result
                                    and other_team_result.school == team_result.school
                                    and other_team_result.rank < old_team_rank):
                                old_team_name = other_team_result.name
                                old_team_rank = other_team_result.rank

                        if old_team_name:
                            # The team did change their name
                            del results_by_team_name[team_name]
                            team_name = old_team_name

                    results_by_team_name[team_name][contest_index] = ExtendedTeamResult(
                        team_result=team_result, contest=contest)

            regional_results = regional.team_results if regional else []
            qualifier_results = qualifier.team_results if qualifier else []
            # Teams that were in the regional but were not in the qualifiers, will push down teams that did not
            # make it to the regional, and all teams that didn't make it to the regional should rank after them
            regional_season_ranks = {}
            rank = 0
            for team in regional_results + qualifier_results:
                if team.name not in regional_season_ranks:
                    rank += 1
                    regional_season_ranks[team.name] = rank

            teams: List[RankedTeam] = []
            for team_name, ext_team_results in results_by_team_name.items():
                school: Optional[School] = next(
                    (result.team_result.school for result in ext_team_results if result),
                    None,
                )
                world_result, championship_result, regional_result, qualifier_result = ext_team_results

                regional_season_rank = regional_season_ranks.get(team_name)
                regional_season_percentile = None
                if regional_season_rank:
                    regional_season_percentile = get_percentile(regional_season_rank, rank)

                teams.append(RankedTeam(name=team_name,
                                        school=school,
                                        qualifier_result=qualifier_result,
                                        regional_result=regional_result,
                                        championship_result=championship_result,
                                        world_result=world_result,
                                        regional_season_rank=regional_season_rank,
                                        regional_season_percentile=regional_season_percentile))

            teams.sort(key=_sort_ranked_team)

            seasons.append(ContestSeason(
                year=year,
                qualifier=qualifier,
                regional=regional,
                championship=championship,
                worlds=worlds,
                teams=teams,
            ))

        return seasons

    def get_contests_by_type(self, contest_type: ContestType) -> List[Contest]:
        return [contest for contest in self._contests if contest.type == contest_type]

    def _get_school(self, name: str) -> Optional[School]:
        return self._schools_by_name.get(normalize_school_name(name))

    def get_schools_by_country(self, country: str) -> List[School]:
        return [school for school in self._schools if school.country == country and school.is_eligible]

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
