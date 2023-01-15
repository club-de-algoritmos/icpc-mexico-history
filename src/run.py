import dataclasses
import json
import os

from icpc_mexico.processor import get_mexico_contests


def _get_relative_filename(filename: str) -> str:
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, filename)


if __name__ == '__main__':
    contests = get_mexico_contests(_get_relative_filename('icpc_mexico_contests.csv'))
    contests_as_dicts = [dataclasses.asdict(contest) for contest in contests]
    with open(_get_relative_filename('icpc_mexico_results.json'), 'w') as results_file:
        results_file.write(json.dumps(contests_as_dicts, indent=2, ensure_ascii=False))
