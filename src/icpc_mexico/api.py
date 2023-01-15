from typing import List

import requests

from icpc_mexico.data import Team
from icpc_mexico.errors import IcpcApiError

_PAGE_SIZE = 1000


def get_contest_teams(contest_id: int) -> List[Team]:
    response = requests.get(f'https://icpc.global/api/contest/public/search/contest/{contest_id}'
                            f'?q=sort:rank+asc'
                            f'&page=1'
                            f'&size={_PAGE_SIZE}')
    if not response.ok:
        raise IcpcApiError(f'Could not get contest {contest_id} from ICPC;'
                           f' status code: {response.status_code}, content: {response.content}')

    teams: List[Team] = []
    for team_json in response.json():
        teams.append(Team.from_json(team_json))
    return teams
