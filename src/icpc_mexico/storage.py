import dataclasses
import json
from typing import List

from icpc_mexico.data import FinishedContest


def store_contests(contests: List[FinishedContest], filename: str) -> None:
    contests_as_dicts = [contest.to_dict() for contest in contests]
    with open(filename, 'w') as results_file:
        json.dump(contests_as_dicts, fp=results_file, indent=2, ensure_ascii=False)


def load_contests(filename: str) -> List[FinishedContest]:
    with open(filename, 'r') as results_file:
        contests_dicts = json.load(results_file)

    contests = []
    for contest_dict in contests_dicts:
        contests.append(FinishedContest.from_dict(contest_dict))
    return contests
