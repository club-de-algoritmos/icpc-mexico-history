from typing import List, Any

import requests

from icpc_mexico.data import TeamResult
from icpc_mexico.errors import IcpcApiError

_PAGE_SIZE = 1000


def _from_json_to_team_result(json: Any) -> TeamResult:
    return TeamResult(
        id=json['teamId'],
        name=json['teamName'],
        institution=json['institution'],
        rank=json['rank'],
        problems_solved=json['problemsSolved'],
        total_time=json['totalTime'],
        last_problem_time=json['lastProblemTime'],
        medal_citation=json['medalCitation'],
        site_citation=json['siteCitation'],
        citation=json['citation'],
    )


def get_contest_team_results(contest_id: int) -> List[TeamResult]:
    response = requests.get(f'https://icpc.global/api/contest/public/search/contest/{contest_id}'
                            f'?q=sort:rank+asc'
                            f'&page=1'
                            f'&size={_PAGE_SIZE}')
    if not response.ok:
        raise IcpcApiError(f'Could not get contest {contest_id} from ICPC;'
                           f' status code: {response.status_code}, content: {response.content}')

    teams: List[TeamResult] = []
    for team_json in response.json():
        teams.append(_from_json_to_team_result(team_json))

    if len(teams) == _PAGE_SIZE:
        raise IcpcApiError(f'Response page was full for contest {contest_id}, got {_PAGE_SIZE} team results')

    return teams
