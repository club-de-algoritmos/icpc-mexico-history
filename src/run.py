import os

from icpc_mexico import processor, storage


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

    schools = processor.get_schools(contests)
    storage.store_schools(schools, _get_data_filename('icpc_mexico_schools'))
