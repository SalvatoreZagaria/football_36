import random
import typing as t
import logging
import traceback

import sqlalchemy
from sqlalchemy import func, select

from app import model as m, app_config as config
from app.utils import neo4j_client

logger = logging.getLogger()

MINIMUM_PLAYER_VALUE = config.get_minimum_player_value()
MINIMUM_PLAYER_VALUE_WITH_LEAGUES_FILTER = config.get_minimum_player_value_with_leagues_filter()
PLAYERS_SELECTION_LIMIT = config.players_selection_limit()
MAXIMUM_PATH_LENGTH = config.get_maximum_path_length()
CHALLENGE_GENERATION_ATTEMPTS = 10


def select_players_for_challenge(leagues_filter: t.List[int] = None
                                 ) -> t.Tuple[t.Optional[m.Player], t.Optional[m.Player]]:
    if leagues_filter:
        minimum_player_value = MINIMUM_PLAYER_VALUE_WITH_LEAGUES_FILTER

        league_years = select(m.LeagueSeasons.league_id, func.max(m.LeagueSeasons.year).label('max_year')
                              ).group_by(m.LeagueSeasons.league_id)
        if leagues_filter:
            league_years = league_years.filter(m.LeagueSeasons.league_id.in_(leagues_filter))
        league_years = league_years.cte('league_years')

        max_seasons = select(m.LeagueSeasons).select_from(
            league_years.join(m.LeagueSeasons, sqlalchemy.and_(
                league_years.columns.league_id == m.LeagueSeasons.league_id,
                league_years.columns.max_year == m.LeagueSeasons.year), isouter=True)).cte('max_seasons')

        max_year_teams = select(max_seasons, m.TeamMilitancy.team_id).select_from(
            max_seasons.join(m.TeamMilitancy, sqlalchemy.and_(max_seasons.columns.league_id == m.TeamMilitancy.league_id,
                                                              max_seasons.columns.year == m.TeamMilitancy.year),
                             isouter=True)).cte('max_year_teams')

        militancies = select(m.Militancy.player_id).select_from(max_year_teams.join(
            m.Militancy, sqlalchemy.and_(max_year_teams.columns.team_id == m.Militancy.team_id,
                                         max_year_teams.columns.end_date == m.Militancy.end_date), isouter=True
        )).cte('militancies')

        players = select(m.Player).filter(m.Player.id.in_(sqlalchemy.select(militancies))).cte('players')
    else:
        minimum_player_value = MINIMUM_PLAYER_VALUE

        players = select(m.Player).cte('players')

    avg_value = m.db.session.query(func.avg(players.columns.value)).scalar_subquery()

    high_value_players = m.db.session.query(players.columns.id, players.columns.value).filter(
        players.columns.value > func.greatest(avg_value, minimum_player_value)).order_by(
        players.columns.value.desc()).limit(PLAYERS_SELECTION_LIMIT).all()

    player_ids = [r[0] for r in high_value_players]
    player_values = [r[1] for r in high_value_players]

    for _ in range(CHALLENGE_GENERATION_ATTEMPTS):
        p1, p2 = random.choices(player_ids, weights=player_values, k=2)

        if neo4j_client.validate_path_for_challenge_creation(p1, p2, MAXIMUM_PATH_LENGTH):
            p1 = m.db.session.query(m.Player).get(p1)
            p2 = m.db.session.query(m.Player).get(p2)

            return p1, p2

    return None, None


def generate_challenge(leagues_filter: t.List = None) -> t.Optional[t.Tuple[m.Player, m.Player]]:
    p1, p2 = select_players_for_challenge(leagues_filter=leagues_filter)
    if not all((p1, p2)):
        logger.warning('Could not generate challenge - Maximum attempts reached')
        return None

    return p1, p2


def get_optimal_path(player_id_1: t.Union[str, int], player_id_2: t.Union[str, int]
                     ) -> t.Optional[t.List[t.Dict[str, int]]]:
    records = neo4j_client.shortest_path(player_id_1, player_id_2)
    if not records:
        return None
    max_weight = max([r[1] for r in records])
    records = [r for r in records if r[1] == max_weight]
    pick = random.choice(records)

    res = []
    try:
        for rel in pick[0].relationships:
            res.append({
                'start': int(rel.start_node._properties['playerId']),
                'team': int(rel._properties['team_id']),
                'end': int(rel.end_node._properties['playerId']),
            })
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.error(f'Error while getting shortest path -> {e}', extra={
            'start': player_id_1, 'end': player_id_2, 'stacktrace': stack_trace
        })
        return None

    return res
