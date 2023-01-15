import csv
import os
from typing import List

from icpc_mexico import api
from icpc_mexico.data import ContestMetadata, Contest


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


def query_contests() -> None:
    metadata = _get_contest_metadata(_get_relative_filename('icpc_mexico_contests.csv'))
    print(f'Metadata size: {len(metadata)}')

    contests = []
    for contest_metadata in metadata:
        print(f'Getting results for contest {contest_metadata.name}')
        teams = api.get_contest_teams(contest_metadata.id)
        contests.append(Contest(metadata=contest_metadata, teams=teams))
