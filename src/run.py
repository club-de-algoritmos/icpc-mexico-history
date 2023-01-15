import os

from icpc_mexico.processor import get_mexico_contests
from icpc_mexico.storage import store_contests, load_contests


def _get_data_filename(filename: str) -> str:
    return os.path.join(os.getcwd(), 'data', filename)


if __name__ == '__main__':
    contests_filename = _get_data_filename('icpc_mexico_results.json')

    contests = get_mexico_contests(_get_data_filename('icpc_mexico_contests.csv'))
    store_contests(contests, contests_filename)

    loaded_contests = load_contests(contests_filename)
    if contests != loaded_contests:
        raise Exception('Could not load correctly')
