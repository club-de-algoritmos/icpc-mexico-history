import json
from typing import List, Any

from icpc_mexico.data import FinishedContest, School


def _store(objects: List[Any], filename: str) -> None:
    dicts = [obj.to_dict() for obj in objects]
    with open(filename, 'w') as f:
        json.dump(dicts, fp=f, indent=2, ensure_ascii=False)


def _load(cls: Any, filename: str) -> List:
    with open(filename, 'r') as f:
        dicts = json.load(f)

    objects = []
    for d in dicts:
        objects.append(cls.from_dict(d))
    return objects


def store_contests(contests: List[FinishedContest], filename: str) -> None:
    _store(contests, filename)


def load_contests(filename: str) -> List[FinishedContest]:
    return _load(FinishedContest, filename)


def store_schools(schools: List[School], filename: str) -> None:
    _store(schools, filename)


def load_schools(filename: str) -> List[School]:
    return _load(School, filename)
