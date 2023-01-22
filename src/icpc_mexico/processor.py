import csv
import dataclasses
import json
from collections import defaultdict
from typing import List, Dict, Optional

from icpc_mexico import icpc_api
from icpc_mexico.data import Contest, FinishedContest, TeamResult, ContestType, School, SchoolCommunity, MEXICO
from icpc_mexico.errors import ProcessingError
from icpc_mexico.utils import normalize_str


def _from_csv_to_contest(csv_row: Dict) -> Contest:
    return Contest(
        id=int(csv_row['id']),
        url_id=csv_row['url_id'],
        name=csv_row['name'],
        year=int(csv_row['year']),
        date=csv_row['date'],
        type=ContestType(csv_row['type']),
        comments=csv_row['comments'],
    )


def _get_contests(filename: str) -> List[Contest]:
    contests: List[Contest] = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for csv_row in csv_reader:
            contests.append(_from_csv_to_contest(csv_row))

    return contests


def _clean_up_teams(team_results: List[TeamResult], contest: Contest) -> List[TeamResult]:
    unique_teams: Dict[int, TeamResult] = {}
    teams_without_rank = []
    last_rank = 0
    for team in team_results:
        if not team.rank:
            teams_without_rank.append(team)
            continue

        last_rank = max(last_rank, team.rank)
        if team.id not in unique_teams:
            unique_teams[team.id] = team
            continue
        older_team = unique_teams[team.id]
        if (older_team.problems_solved < team.problems_solved
                or older_team.total_time > team.total_time
                or older_team.last_problem_time > team.last_problem_time):
            unique_teams[team.id] = team

    # Some teams have no rank, so they should be after the largest rank seen
    for team in teams_without_rank:
        if team.id not in unique_teams:
            unique_teams[team.id] = dataclasses.replace(team, rank=last_rank + 1)

    sorted_teams = sorted(unique_teams.values(), key=lambda t: t.rank)
    prev_team = None
    for idx, team in enumerate(sorted_teams):
        expected_rank = idx + 1
        # Allow a rank offset of up to 5 places as that's how it is :(
        if team.rank != expected_rank and not (prev_team.rank <= team.rank <= prev_team.rank + 5):
            print(f'Previous team: {prev_team}')
            print(f'Team: {team}')
            raise ProcessingError(f'Unexpected rank for team {team.name}: {team.rank}, expected {expected_rank}')
        prev_team = team

    return sorted_teams


def get_finished_contests(contest_csv_filename: str) -> List[FinishedContest]:
    contests = _get_contests(contest_csv_filename)
    print(f'Found {len(contests)} contests to query results for')

    finished_contests = []
    for contest in contests:
        if contest.comments.startswith('TBD'):
            continue

        print(f'Getting results for contest {contest.name}')
        teams = icpc_api.get_contest_team_results(contest.id)
        if not teams:
            raise ProcessLookupError(f'Contest {contest.name} has no team results')

        unique_teams = _clean_up_teams(teams, contest)
        if len(unique_teams) != len(teams):
            print(f'Removed {len(teams) - len(unique_teams)} ({len(teams)} -> {len(unique_teams)})'
                  f' duplicate teams from contest {contest.name}')

        finished_contests.append(FinishedContest.from_contest(contest=contest, team_results=unique_teams))

    return finished_contests


def _get_school(school_name: str, schools: List[School]) -> Optional[School]:
    school_name = normalize_str(school_name)
    for school in schools:
        if school.matches_name(school_name):
            return school
    return None


def get_schools(contests: List[FinishedContest]) -> List[School]:
    print(f'Getting schools from {len(contests)} contests')
    schools = [
        School(
            name='unknown',
            is_eligible=False,
        ),
        School(
            name='bina nusantara university',
        ),
        School(
            name='instituto tecnologico de santo domingo',
            country='dominican republic',
        ),
        School(
            name='universidad nacional de cordoba - famaf',
            country='argentina',
        ),
        School(
            name='universidad nacional autonoma de nicaragua, managua',
            country='nicaragua',
        ),
        School(
            name='faculdade metropolitana de belo horizonte',
            country='brazil',
        ),
        School(
            name='universidad central "marta abreu" de las villas',
            country='cuba',
        ),
        School(
            name='universidad de pinar del rio',
            country='cuba',
        ),
        School(
            name='universidad nacional de ingenieria - fc',
            country='peru',
        ),
        School(
            name='benemerita universidad autonoma de puebla',
            alt_names=['buap facultad de ciencias de la computacion'],
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico superior de poza rica',
            alt_names=['insituto tecnologico superior de poza rica'],
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico superior de irapuato',
            alt_names=['instituto tecnologioco superior de irapuato'],
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico superior de la region de los llanos',
            alt_names=['instituto tecnolãgico superior de la regiãn de los llanos'],
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico de san luis potosi',
            alt_names=['institutuo technologico de san luis potosi'],
            country=MEXICO,
        ),
        School(
            name='escuela preparatoria 5 universidad de guadalajara',
            is_eligible=True,
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico de comitan',
            alt_names=['tec. de comitan.'],
            community=SchoolCommunity.TECNM,
            country=MEXICO,
        ),
        School(
            name='instituto tecnologico autonomo de mexico',
            country=MEXICO,
        ),
    ]

    school_names = set()
    for contest in contests:
        if contest.type in [ContestType.WORLD, ContestType.CHAMPIONSHIP]:
            continue
        for team in contest.team_results:
            school_names.add(normalize_str(team.institution))

    for school_name in sorted(school_names):
        if _get_school(school_name, schools):
            continue

        if 'costa rica' in school_name:
            schools.append(School(name=school_name, country='costa rica'))
            continue

        if ('habana' in school_name
                or school_name.startswith('universidad de las ciencias informaticas')
                or school_name.startswith('universidad de oriente')):
            schools.append(School(name=school_name, country='cuba'))
            continue

        if (school_name.startswith('tecnologico nacional de mexico')
                or school_name.startswith('tecnm')
                or school_name.startswith('instituto tecnologico')
                or school_name.startswith('instituto technologico')):
            schools.append(School(name=school_name, community=SchoolCommunity.TECNM, country=MEXICO))
            continue

        if school_name.startswith('itesm'):
            schools.append(School(name=school_name, community=SchoolCommunity.ITESM, country=MEXICO))
            continue

        if school_name.startswith('universidad politecnica'):
            schools.append(School(name=school_name, community=SchoolCommunity.POLITECNICA, country=MEXICO))
            continue

        if school_name.startswith('olimpiada') or school_name.startswith('cetis') or school_name.startswith('cbtis'):
            schools.append(School(name=school_name, is_eligible=False, country=MEXICO))
            continue

        schools.append(School(name=school_name, country=MEXICO))

    print(f'Found {len(schools)} schools')
    return sorted(schools, key=lambda s: s.name)


def compute_extra_team_results(contests: List[FinishedContest], schools: List[School]) -> List[FinishedContest]:
    print(f'Computing extra team results for {len(contests)} contests')
    computed_contests = []
    for contest in contests:
        community_rank: Dict[SchoolCommunity, int] = defaultdict(int)
        country_rank: Dict[str, int] = defaultdict(int)
        # TODO: Compute
        # super_region_ranking: Dict[SuperRegion, int] = defaultdict(int)
        team_results = []
        for team in contest.team_results:
            school = _get_school(team.institution, schools)

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
                team = dataclasses.replace(team,
                                           community=school.community,
                                           community_rank=community_rank[school.community])

            if contest.type == ContestType.WORLD:
                country_rank[school.country] += 1
                team = dataclasses.replace(team,
                                           country=school.country,
                                           country_rank=country_rank[school.country])

            team_results.append(team)

        computed_contests.append(dataclasses.replace(contest, team_results=team_results))

    return computed_contests
