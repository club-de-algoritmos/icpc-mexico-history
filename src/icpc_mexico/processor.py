import csv
import dataclasses
import json
import os
from typing import List, Dict

from icpc_mexico import api
from icpc_mexico.data import ContestMetadata, Contest, Team
from icpc_mexico.errors import ProcessingError


def _get_relative_filename(filename: str) -> str:
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, filename)


def _get_contest_metadata(filename: str) -> List[ContestMetadata]:
    contests: List[ContestMetadata] = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for csv_row in csv_reader:
            contest = ContestMetadata.from_csv(csv_row)
            contests.append(contest)

    return contests


def _remove_duplicate_teams(teams: List[Team]) -> List[Team]:
    unique_teams: Dict[int, Team] = {}
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


def get_mexico_contests() -> List[Contest]:
    metadata = _get_contest_metadata(_get_relative_filename('icpc_mexico_contests.csv'))
    print(f'Metadata size: {len(metadata)}')

    contests = []
    for contest_metadata in metadata:
        if contest_metadata.name != 'The 2009 Mexico & Central America Contest':
            continue
        print(f'Getting results for contest {contest_metadata.name}')
        teams = api.get_contest_teams(contest_metadata.id)
        if not teams:
            raise ProcessLookupError(f'Contest {contest_metadata.name} has no team results')

        unique_teams = _remove_duplicate_teams(teams)
        if len(unique_teams) != len(teams):
            print(f'Removed {len(teams) - len(unique_teams)} ({len(teams)} -> {len(unique_teams)})'
                  f' duplicate teams from contest {contest_metadata.name}')

        contests.append(Contest(metadata=contest_metadata, teams=unique_teams))

    # print(json.dumps(dataclasses.asdict(contests[0])))
    return contests
