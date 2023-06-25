#! /usr/bin/env python

import argparse
import os
from typing import List, Tuple

from icpc_mexico import processor, storage
from icpc_mexico.analysis import Analyzer
from icpc_mexico.data import FinishedContest, School, MEXICO
from icpc_mexico.queries import Queries
from icpc_mexico.utils import log_run_time


def _get_filename(filename: str, path: str = 'data') -> str:
    return os.path.join(os.getcwd(), path, filename)


@log_run_time
def _get_contests(refresh_contests: bool) -> Tuple[List[FinishedContest], bool]:
    contests = processor.get_contests(_get_filename('icpc_mexico_contests.csv'))
    contests_filename = _get_filename('icpc_mexico_results.json')
    contests_updated = False
    if refresh_contests or not os.path.exists(contests_filename):
        contests_updated = True
        if refresh_contests:
            print('Refreshing contest data, querying the ICPC API')
        else:
            print(f'No contest data found in file {contests_filename}, querying the ICPC API')
        finished_contests = processor.get_finished_contests(contests)
        storage.store_contests(finished_contests, contests_filename)
    else:
        print(f'Contest data found in file {contests_filename}, loading it')
        finished_contests = storage.load_contests(contests_filename)
        finished_contest_ids = {contest.id for contest in finished_contests}
        missing_contests = [
            contest
            for contest in contests
            if contest.id not in finished_contest_ids and contest.date != 'TBD'
        ]
        if missing_contests:
            missing_contest_desc = ", ".join(sorted(contest.name for contest in missing_contests))
            print(f'{len(missing_contests)} contests are missing: {missing_contest_desc}')

            finished_contests += processor.get_finished_contests(missing_contests)
            storage.store_contests(finished_contests, contests_filename)
            contests_updated = True
    return finished_contests, contests_updated


@log_run_time
def _get_schools(refresh_schools: bool, contests: List[FinishedContest]) -> List[School]:
    schools_filename = _get_filename('icpc_mexico_schools.json')
    if refresh_schools or not os.path.exists(schools_filename):
        if refresh_schools:
            print('Refreshing school data, calculating it')
        else:
            print(f'No school data found in file {schools_filename}, calculating it')
        schools = processor.get_schools(contests)
        storage.store_schools(schools, schools_filename)
    else:
        print(f'School data found in file {schools_filename}, loading it')
        schools = storage.load_schools(schools_filename)
    return schools


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-contests", action='store_true', default=False,
                        help="Refresh the contest data by querying the ICPC API")
    parser.add_argument("--refresh-schools", action='store_true', default=False,
                        help="Refresh the school data by rebuilding it")
    parser.add_argument("--refresh-school-history", action='store_true', default=False,
                        help="Refresh the school participation history by rebuilding it")
    args = parser.parse_args()

    all_contests, contests_were_updated = _get_contests(args.refresh_contests)

    should_refresh_schools = args.refresh_schools or contests_were_updated
    all_schools = _get_schools(should_refresh_schools, all_contests)

    queries = Queries(all_contests, all_schools)
    analyzer = Analyzer(queries=queries, analysis_path=_get_filename('', path='analysis'))
    analyzer.analyze()

    should_refresh_school_history = args.refresh_school_history or should_refresh_schools
    if should_refresh_school_history:
        analyzer.analyze_schools_by_country(MEXICO)
