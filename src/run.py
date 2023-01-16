import os

from icpc_mexico.processor import get_finished_contests
from icpc_mexico.storage import store_contests, load_contests


def _get_data_filename(filename: str) -> str:
    return os.path.join(os.getcwd(), 'data', filename)


if __name__ == '__main__':
    contests_filename = _get_data_filename('icpc_mexico_results.json')
    if os.path.exists(contests_filename):
        print(f'Contest data found in file {contests_filename}, loading it')
        contests = load_contests(contests_filename)
    else:
        print(f'No contest data found in file {contests_filename}, querying the ICPC API for it')
        contests = get_finished_contests(_get_data_filename('icpc_mexico_contests.csv'))
        store_contests(contests, contests_filename)
