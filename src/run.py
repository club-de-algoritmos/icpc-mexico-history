#! /usr/bin/env python

import os
import argparse

from icpc_mexico import processor, storage, analysis


def _get_data_filename(filename: str) -> str:
    return os.path.join(os.getcwd(), 'data', filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-contests", action='store_true', default=False,
                        help="Refresh the contest data by querying the ICPC API")
    parser.add_argument("--refresh-schools", action='store_true', default=False,
                        help="Refresh the school data by rebuilding it")
    args = parser.parse_args()

    contests_filename = _get_data_filename('icpc_mexico_results.json')
    if args.refresh_contests or not os.path.exists(contests_filename):
        if args.refresh_contests:
            print('Refreshing contest data, querying the ICPC API')
        else:
            print(f'No contest data found in file {contests_filename}, querying the ICPC API')
        contests = processor.get_finished_contests(_get_data_filename('icpc_mexico_contests.csv'))
        storage.store_contests(contests, contests_filename)
    else:
        print(f'Contest data found in file {contests_filename}, loading it')
        contests = storage.load_contests(contests_filename)

    schools_filename = _get_data_filename('icpc_mexico_schools.json')
    if args.refresh_schools or not os.path.exists(contests_filename):
        if args.refresh_schools:
            print('Refreshing school data, calculating it')
        else:
            print(f'No school data found in file {schools_filename}, calculating it')
        schools = processor.get_schools(contests)
        storage.store_schools(schools, schools_filename)
    else:
        print(f'School data found in file {schools_filename}, loading it')
        schools = storage.load_schools(schools_filename)

    with open(_get_data_filename('mexico_analysis.txt'), 'w') as analysis_file:
        contests = processor.compute_extra_team_results(contests, schools)
        analysis.analyze(contests, analysis_file)

        for school_name in [
                'Instituto Tecnológico de Ciudad Madero',
                'Instituto Tecnológico de Culiacán',
                'Instituto Tecnológico Superior del Sur de Guanajuato']:
            analysis.analyze_school(school_name, contests, analysis_file)
