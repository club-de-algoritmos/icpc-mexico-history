import csv
import dataclasses
from typing import List, Dict

from icpc_mexico import icpc_api
from icpc_mexico.data import Contest, FinishedContest, TeamResult, ContestType
from icpc_mexico.errors import ProcessingError


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


def _remove_duplicate_teams(teams: List[TeamResult]) -> List[TeamResult]:
    unique_teams: Dict[int, TeamResult] = {}
    teams_without_rank = []
    last_rank = 0
    for team in teams:
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
        teams = api.get_contest_team_results(contest.id)
        if not teams:
            raise ProcessLookupError(f'Contest {contest.name} has no team results')

        unique_teams = _remove_duplicate_teams(teams)
        if len(unique_teams) != len(teams):
            print(f'Removed {len(teams) - len(unique_teams)} ({len(teams)} -> {len(unique_teams)})'
                  f' duplicate teams from contest {contest.name}')

        finished_contests.append(FinishedContest.from_contest(contest=contest, team_results=unique_teams))

    return finished_contests
