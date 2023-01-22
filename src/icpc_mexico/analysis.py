from typing import List

from icpc_mexico.data import FinishedContest, ContestType, SchoolCommunity


def analyze(contests: List[FinishedContest]) -> None:
    print(f'Analyzing results...')

    print('Mexico in the World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue
        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.country != 'mexico':
                continue
            community_desc = f', {team.community}' if team.community else ''
            print(f'    {team.rank} ({team.country_rank}) {team.name} ({team.institution}{community_desc})')
    print()

    print('TecNM in World Finals:')
    for contest in contests:
        if contest.type != ContestType.WORLD:
            continue
        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            print(f'    {team.rank} ({team.country_rank}) {team.name} ({team.institution})')
    print()

    print('Top 20 TecNM in Mexico Finals:')
    for contest in contests:
        if contest.type != ContestType.REGIONAL:
            continue
        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 20:
                break
            print(f'    {team.rank} ({team.community_rank}) {team.name} ({team.institution})')
    print()

    print('Top 10 TecNM in Mexico Qualifiers:')
    for contest in contests:
        if contest.type not in [ContestType.GRAN_PREMIO, ContestType.PROGRAMMING_BATTLE]:
            continue
        print(f'  {contest.name}:')
        for team in contest.team_results:
            if team.community != SchoolCommunity.TECNM:
                continue
            if team.community_rank > 10:
                break
            print(f'    {team.rank} ({team.community_rank}) {team.name} ({team.institution})')
    print()
