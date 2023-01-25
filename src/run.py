#! /usr/bin/env python

import os
import argparse
from typing import List

from icpc_mexico import processor, storage, analysis
from icpc_mexico.data import FinishedContest, School


def _get_data_filename(filename: str) -> str:
    return os.path.join(os.getcwd(), 'data', filename)


def _get_contests(refresh_contests: bool) -> List[FinishedContest]:
    contests_filename = _get_data_filename('icpc_mexico_results.json')
    if refresh_contests or not os.path.exists(contests_filename):
        if refresh_contests:
            print('Refreshing contest data, querying the ICPC API')
        else:
            print(f'No contest data found in file {contests_filename}, querying the ICPC API')
        contests = processor.get_finished_contests(_get_data_filename('icpc_mexico_contests.csv'))
        storage.store_contests(contests, contests_filename)
    else:
        print(f'Contest data found in file {contests_filename}, loading it')
        contests = storage.load_contests(contests_filename)
    return contests


def _get_schools(refresh_schools: bool, contests: List[FinishedContest]) -> List[School]:
    schools_filename = _get_data_filename('icpc_mexico_schools.json')
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
    args = parser.parse_args()

    all_contests = _get_contests(args.refresh_contests)
    all_schools = _get_schools(args.refresh_schools, all_contests)
    with open(_get_data_filename('mexico_analysis.txt'), 'w') as analysis_file:
        all_contests = processor.compute_extra_team_results(all_contests, all_schools)
        analysis.analyze(all_contests, all_schools, analysis_file)
