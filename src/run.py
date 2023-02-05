#! /usr/bin/env python

import argparse
import os
from typing import List

from icpc_mexico import processor, storage
from icpc_mexico.analysis import Analyzer
from icpc_mexico.data import FinishedContest, School, MEXICO
from icpc_mexico.queries import Queries
from icpc_mexico.utils import log_run_time


def _get_filename(filename: str, path: str = 'data') -> str:
    return os.path.join(os.getcwd(), path, filename)


@log_run_time
def _get_contests(refresh_contests: bool) -> List[FinishedContest]:
    contests_filename = _get_filename('icpc_mexico_results.json')
    if refresh_contests or not os.path.exists(contests_filename):
        if refresh_contests:
            print('Refreshing contest data, querying the ICPC API')
        else:
            print(f'No contest data found in file {contests_filename}, querying the ICPC API')
        contests = processor.get_finished_contests(_get_filename('icpc_mexico_contests.csv'))
        storage.store_contests(contests, contests_filename)
    else:
        print(f'Contest data found in file {contests_filename}, loading it')
        contests = storage.load_contests(contests_filename)
    return contests


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

    should_refresh_contests = args.refresh_contests
    should_refresh_schools = args.refresh_schools or should_refresh_contests
    should_refresh_school_history = args.refresh_school_history or should_refresh_schools

    all_contests = _get_contests(should_refresh_contests)
    all_schools = _get_schools(should_refresh_schools, all_contests)
    queries = Queries(all_contests, all_schools)

    analyzer = Analyzer(queries=queries, analysis_path=_get_filename('', path='analysis'))
    analyzer.analyze()
    if should_refresh_school_history:
        analyzer.analyze_schools_by_country(MEXICO)
