from typing import List, Any

import requests

from icpc_mexico.data import TeamResult, ContestSite, ContestSiteTeam
from icpc_mexico.errors import IcpcApiError

_PAGE_SIZE = 10000


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
    url = (f'https://icpc.global/api/contest/public/search/contest/{contest_id}'
           f'?q=sort:rank+asc,problemsSolved+desc,totalTime+asc,lastProblemTime+asc'
           f'&page=1'
           f'&size={_PAGE_SIZE}')
    response = requests.get(url)
    if not response.ok:
        raise IcpcApiError(f'Could not get contest {contest_id} from ICPC;'
                           f' status code: {response.status_code}, content: {response.content}')

    teams: List[TeamResult] = []
    for team_json in response.json():
        teams.append(_from_json_to_team_result(team_json))

    if len(teams) == _PAGE_SIZE:
        raise IcpcApiError(f'Response page was full for contest {contest_id}, got {_PAGE_SIZE} team results')

    return teams


def _from_json_to_contest_site(json: Any) -> ContestSite:
    return ContestSite(
        id=json['id'],
        name=json['name'],
        homepage=json['homepage'],
        date=json['date'],
        email=json['email'],
        type=json['type'],
    )


def get_sites(contest_url_id: str) -> List[ContestSite]:
    url = f'https://icpc.global/api/contest/public/{contest_url_id}/sites'
    response = requests.get(url)
    if not response.ok:
        raise IcpcApiError(f'Could not get sites of contest {contest_url_id} from ICPC;'
                           f' status code: {response.status_code}, content: {response.content}')

    sites: List[ContestSite] = []
    for site_json in response.json():
        sites.append(_from_json_to_contest_site(site_json))

    return sites


def _from_json_to_contest_site_team(json: Any) -> ContestSiteTeam:
    return ContestSiteTeam(
        id=json['teamId'],
        name=json['name'],
        status=json['status'],
        country=json['country'],
        institution=json['institution'],
    )


def get_contest_site_teams(site_id: int) -> List[ContestSiteTeam]:
    url = (f'https://icpc.global/api/team/search/site/accepted/{site_id}'
           f'?q=proj:institution,name,teamId%3B'
           f'&page=1'
           f'&size={_PAGE_SIZE}')
    response = requests.get(url)
    if not response.ok:
        raise IcpcApiError(f'Could not get teams of contest site {site_id} from ICPC;'
                           f' status code: {response.status_code}, content: {response.content}')

    teams: List[ContestSiteTeam] = []
    for team_json in response.json():
        teams.append(_from_json_to_contest_site_team(team_json))

    if len(teams) == _PAGE_SIZE:
        raise IcpcApiError(f'Response page was full for contest site {site_id}, got {_PAGE_SIZE} team results')

    return teams
