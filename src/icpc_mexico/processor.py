import csv
import dataclasses
from typing import List, Dict

from icpc_mexico import icpc_api
from icpc_mexico.data import Contest, FinishedContest, TeamResult, ContestType, School, SchoolCommunity, MEXICO
from icpc_mexico.errors import ProcessingError
from icpc_mexico.queries import get_school
from icpc_mexico.utils import normalize_school_name, contains_strings


def _from_csv_to_contest(csv_row: Dict) -> Contest:
    return Contest(
        id=int(csv_row['id']),
        url_id=csv_row['url_id'],
        name=csv_row['name'],
        year=int(csv_row['year']),
        date=csv_row['date'],
        type=ContestType(csv_row['type']),
        comments=csv_row['comments'],
    )


def get_contests(filename: str) -> List[Contest]:
    contests: List[Contest] = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for csv_row in csv_reader:
            contests.append(_from_csv_to_contest(csv_row))

    return contests


def _clean_up_teams(team_results: List[TeamResult], contest: Contest) -> List[TeamResult]:
    unique_teams: Dict[int, TeamResult] = {}
    teams_without_rank = []
    last_rank = 0
    for team in team_results:
        if not team.rank:
            teams_without_rank.append(team)
            continue

        last_rank = max(last_rank, team.rank)
        if team.id not in unique_teams:
            unique_teams[team.id] = team
            continue
        older_team = unique_teams[team.id]
        if (older_team.problems_solved < team.problems_solved
                or older_team.total_time > team.total_time
                or older_team.last_problem_time > team.last_problem_time):
            unique_teams[team.id] = team

    # Some teams have no rank, so they should be after the largest rank seen
    for team in teams_without_rank:
        if team.id not in unique_teams:
            unique_teams[team.id] = dataclasses.replace(team, rank=last_rank + 1)

    sorted_teams = sorted(unique_teams.values(), key=lambda t: t.rank)
    if not contest.is_manual:
        # Check ranks
        prev_team = None
        for idx, team in enumerate(sorted_teams):
            expected_rank = idx + 1
            # Allow a rank offset of up to 5 places as that's how it is :(
            if team.rank != expected_rank and not (prev_team.rank <= team.rank <= prev_team.rank + 5):
                print(f'Previous team: {prev_team}')
                print(f'Team: {team}')
                raise ProcessingError(f'Unexpected rank for team {team.name}: {team.rank}, expected {expected_rank}')
            prev_team = team

    return sorted_teams


def _get_teams_without_api(contest: Contest) -> List[TeamResult]:
    """There is no API data for these contests, so they are manually added as there is a record of it.

    There is no API data for contests for 1998 or earlier, but they can be consulted manually, for example, at
    https://icpc.global/community/results-1998
    """
    if contest.url_id == 'World-Finals-1998':
        return [
            TeamResult(id=0, name='<Desconocido>', institution='ITESM Campus Monterrey',
                       rank=40, problems_solved=2, total_time=None,
                       last_problem_time=None, medal_citation=None, site_citation=None, citation=None),
        ]
    if contest.url_id == 'World-Finals-1997':
        return [
            TeamResult(id=0, name='<Desconocido>', institution='Universidad Juarez Autonoma de Tabasco',
                       rank=28, problems_solved=None, total_time=None,
                       last_problem_time=None, medal_citation=None, site_citation=None, citation=None),
        ]
    raise ValueError(f'Unexpected contest without API data: {contest.name}')


def get_finished_contests(contests: List[Contest]) -> List[FinishedContest]:
    print(f'Will query the ICPC API for {len(contests)} contests')
    finished_contests = []
    for contest in contests:
        if contest.comments.startswith('TBD'):
            continue

        if contest.is_manual:
            teams = _get_teams_without_api(contest)
        else:
            print(f'Getting results for contest {contest.name}')
            teams = icpc_api.get_contest_team_results(contest.id)
            if not teams:
                raise ProcessLookupError(f'Contest {contest.name} has no team results')

        unique_teams = _clean_up_teams(teams, contest)
        if len(unique_teams) != len(teams):
            print(f'Removed {len(teams) - len(unique_teams)} ({len(teams)} -> {len(unique_teams)})'
                  f' duplicate teams from contest {contest.name}')

        finished_contests.append(FinishedContest.from_contest(contest=contest, team_results=unique_teams))

    return finished_contests


def get_schools(contests: List[FinishedContest]) -> List[School]:
    print(f'Getting schools from {len(contests)} contests')
    schools = [
        School(
            name='unknown',
            is_eligible=False,
        ),
        School(
            name='Bina Nusantara University',
        ),
        School(
            name='Instituto Tecnológico de Santo Domingo',
            country='dominican republic',
        ),
        School(
            name='Universidad Nacional de Córdoba - FAMAF',
            country='argentina',
        ),
        School(
            name='Universidad Nacional Autónoma de Nicaragua, Managua',
            country='nicaragua',
        ),
        School(
            name='Faculdade Metropolitana de Belo Horizonte',
            country='brazil',
        ),
        School(
            name='Universidad Central "Marta Abreu" de Las Villas',
            country='cuba',
        ),
        School(
            name='Universidad de Pinar del Río',
            country='cuba',
        ),
        School(
            name='Universidad Nacional de Ingeniería - FC',
            country='peru',
        ),
        School(
            name="Binus University",
            country="indonesia",
        ),
        School(
            name='Benemérita Universidad Autónoma de Puebla',
            alt_names=['buap facultad de ciencias de la computacion'],
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico Superior de Poza Rica',
            alt_names=['insituto tecnologico superior de poza rica'],
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico Superior de Irapuato',
            alt_names=['instituto tecnologioco superior de irapuato'],
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico Superior de la Región de los Llanos',
            alt_names=['instituto tecnolãgico superior de la regiãn de los llanos'],
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico de San Luis Potosí',
            alt_names=['institutuo technologico de san luis potosi'],
            country=MEXICO,
        ),
        School(
            name='Escuela Preparatoria 5 Universidad de Guadalajara',
            is_eligible=True,
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico de Comitán',
            alt_names=['tec. de comitan.', 'instituto technologico de comitan'],
            community=SchoolCommunity.TECNM,
            country=MEXICO,
        ),
        School(
            name='Instituto Tecnológico Autónomo de México',
            country=MEXICO,
        ),
        School(
            name='Universidad Autónoma de Occidente',
            country=MEXICO,
            state='sinaloa',
        ),
        School(
            name='Instituto Tecnológico de Mazatlán',
            community=SchoolCommunity.TECNM,
            country=MEXICO,
            state='sinaloa',
            alt_names=["tecnológico nacional de méxico / instituto tecnológico de mazatlán"],
        ),
        School(
            name='Universidad de Guanajuato - CIMAT',
            alt_names=['universidad de guanajuato', 'universidad de guanajuato - dcne'],
            country=MEXICO,
        ),
        School(
            name='Universidad de Guadalajara CUCEI',
            alt_names=['universidad de guadalajara'],
            country=MEXICO,
        ),
        School(
            name='Universidad Juárez Autónoma de Tabasco',
            country=MEXICO,
        ),
        School(
            name='Centro de Enseñanza Tecnica Industrial - Plantel Tonala',
            country=MEXICO,
            is_eligible=False,
        ),
        School(
            name='Centro de Estudios Tecnológico industrial y de servicios 78',
            country=MEXICO,
            is_eligible=False,
        ),
        School(
            name='CETI Colomos',
            country=MEXICO,
            is_eligible=False,
        ),
        School(
            name='Colegio Anglo',
            country=MEXICO,
            is_eligible=False,
        ),
        School(
            name='The American School Foundation of Guadalajara',
            country=MEXICO,
            is_eligible=False,
        ),
    ]

    school_names = set()
    for contest in contests:
        if contest.type in [ContestType.WORLD, ContestType.CHAMPIONSHIP]:
            continue
        for team in contest.team_results:
            school_names.add(team.institution.strip())

    for school_name in sorted(school_names):
        normalized_name = normalize_school_name(school_name)
        if get_school(normalized_name, schools):
            continue

        if contains_strings(normalized_name, 'costa rica'):
            schools.append(School(name=school_name, country='costa rica'))
            continue

        if contains_strings(normalized_name, 'jamaica'):
            schools.append(School(name=school_name, country='jamaica'))
            continue

        if contains_strings(normalized_name, 'universidad centroamericana', 'universidad gerardo barrios'):
            schools.append(School(name=school_name, country='el salvador'))
            continue

        if contains_strings(normalized_name, 'guatemala', 'universidad rafael landivar', 'universidad mesoamericana'):
            schools.append(School(name=school_name, country='guatemala'))
            continue

        if contains_strings(normalized_name, 'panama', 'universidad internacional de ciencia y tecnologia'):
            schools.append(School(name=school_name, country='panama'))
            continue

        if (contains_strings(normalized_name,
                             'habana',
                             'universidad de las ciencias informaticas',
                             'universidad de oriente',
                             'universidad de cienfuegos',
                             'universidad de guantanamo',
                             'universidad de holguin',
                             'universidad de la isla de la juventud',
                             'camaguey')):
            schools.append(School(name=school_name, country='cuba'))
            continue

        if (contains_strings(normalized_name,
                             'tecnologico nacional de mexico',
                             'tecnm',
                             'instituto tecnologico')):
            # "technologico" -> "tecnologico"
            schools.append(School(
                name=school_name.replace('echno', 'ecno'), community=SchoolCommunity.TECNM, country=MEXICO))
            continue

        if contains_strings(normalized_name, 'itesm'):
            schools.append(School(name=school_name, community=SchoolCommunity.ITESM, country=MEXICO))
            continue

        if contains_strings(normalized_name, 'olimpiada', 'cetis', 'cbtis', 'cecytem', 'bachillerato', 'preparatoria'):
            schools.append(School(name=school_name, is_eligible=False, country=MEXICO))
            continue

        schools.append(School(name=school_name, country=MEXICO))

    processed_schools = []
    state_keywords = {
        'sinaloa': ['culiacan', 'mazatlan', 'sinaloa', 'mochis'],
    }
    for school in schools:
        if school.country != MEXICO or school.state:
            processed_schools.append(school)
            continue

        matched_state = None
        for state, keywords in state_keywords.items():
            for keyword in keywords:
                if keyword in normalize_school_name(school.name):
                    matched_state = state
                    break
            if matched_state:
                break

        processed_schools.append(dataclasses.replace(school, state=matched_state))

    print(f'Found {len(processed_schools)} schools')
    return sorted(processed_schools, key=lambda s: s.name.lower())
