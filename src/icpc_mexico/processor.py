import csv
from typing import List, Dict

from icpc_mexico import api
from icpc_mexico.data import Contest, FinishedContest, TeamResult
from icpc_mexico.errors import ProcessingError


def _get_contests(filename: str) -> List[Contest]:
    contests: List[Contest] = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for csv_row in csv_reader:
            contest = Contest.from_csv(csv_row)
            contests.append(contest)

    return contests


def _remove_duplicate_teams(teams: List[TeamResult]) -> List[TeamResult]:
    unique_teams: Dict[int, TeamResult] = {}
    teams_without_rank = []
    for team in teams:
        if not team.rank:
            teams_without_rank.append(team)
            continue

        if team.id not in unique_teams:
            unique_teams[team.id] = team
            continue
        older_team = unique_teams[team.id]
        if (older_team.rank > team.rank
                or older_team.problems_solved < team.problems_solved
                or older_team.total_time > team.total_time
                or older_team.last_problem_time > team.last_problem_time):
            print(f'A better team was found after in the list')
            print(f'  Seen: {older_team}')
            print(f'  Current: {team}')
            unique_teams[team.id] = team

    for team in teams_without_rank:
        if team.id not in unique_teams:
            raise ProcessingError(f'Team {team.name} does not have a rank at all')

    sorted_teams = sorted(unique_teams.values(), key=lambda t: t.rank)
    last_rank = sorted_teams[-1].rank
    prev_team = None
    for idx, team in enumerate(sorted_teams):
        expected_rank = idx + 1
        if team.rank != expected_rank and team.rank != prev_team.rank and team.rank != last_rank:
            print(f'Team: {team}')
            print(f'Previous team: {prev_team}')
            raise ProcessingError(f'Unexpected rank for team {team.name}: {team.rank}, expected {expected_rank}')
        prev_team = team

    return sorted_teams


def get_mexico_contests(contest_csv_filename: str) -> List[FinishedContest]:
    contests = _get_contests(contest_csv_filename)
    print(f'Contest count: {len(contests)}')

    finished_contests = []
    for contest in contests:
        if contest.name != 'The 2009 Mexico & Central America Contest':
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
