import os

from icpc_mexico import processor, storage, analysis


def _get_data_filename(filename: str) -> str:
    return os.path.join(os.getcwd(), 'data', filename)


if __name__ == '__main__':
    contests_filename = _get_data_filename('icpc_mexico_results.json')
    if os.path.exists(contests_filename):
        print(f'Contest data found in file {contests_filename}, loading it')
        contests = storage.load_contests(contests_filename)
    else:
        print(f'No contest data found in file {contests_filename}, querying the ICPC API for it')
        contests = processor.get_finished_contests(_get_data_filename('icpc_mexico_contests.csv'))
        storage.store_contests(contests, contests_filename)

    schools_filename = _get_data_filename('icpc_mexico_schools.json')
    if not os.path.exists(contests_filename):
        print(f'School data found in file {schools_filename}, loading it')
        schools = storage.load_schools(schools_filename)
    else:
        print(f'No school data found in file {schools_filename}, calculating it')
        schools = processor.get_schools(contests)
        storage.store_schools(schools, schools_filename)

    with open(_get_data_filename('mexico_analysis.txt'), 'w') as analysis_file:
        contests = processor.compute_extra_team_results(contests, schools)
        analysis.analyze(contests, analysis_file)

        for school_name in [
                'Instituto Tecnológico de Ciudad Madero',
                'Instituto Tecnológico de Culiacán',
                'Instituto Tecnológico Superior del Sur de Guanajuato']:
            analysis.analyze_school(school_name, contests, analysis_file)
