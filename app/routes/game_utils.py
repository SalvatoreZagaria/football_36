import typing as t
import logging

import sqlalchemy
from sqlalchemy import func

from app import model as m, app_config as config
from app.utils import neo4j_client


logger = logging.getLogger()


MINIMUM_PLAYER_VALUE = config.get_minimum_player_value()
RANDOM_PLAYERS = config.get_random_players_n_to_choose_from()
MAXIMUM_PATH_LENGTH = config.get_maximum_path_length()
CHALLENGE_GENERATION_ATTEMPTS = 5


def generate_challenge() -> t.Optional[t.Tuple[m.Player, m.Player]]:
    res = None
    found = False
    for _ in range(CHALLENGE_GENERATION_ATTEMPTS):
        cte = m.db.session.query(m.Player, (m.Player.value * func.random()).label('random_value')
                                 ).filter(m.Player.value >= MINIMUM_PLAYER_VALUE).order_by(
            sqlalchemy.text('random_value')).limit(RANDOM_PLAYERS).cte('cte')
        res = m.db.session.query(cte).order_by(func.random()).limit(2).all()
        if not res:
            continue

        p_id_1 = res[0].id
        p_id_2 = res[1].id
        if validate_path(p_id_1, p_id_2):
            found = True
            break
    if not found:
        logger.warning('Could not generate challenge - Maximum attempts reached')
        return None

    return tuple(res)


def validate_path(player_id_1: int, player_id_2: int):
    return neo4j_client.validate_path_for_challenge_creation(player_id_1, player_id_2, MAXIMUM_PATH_LENGTH)
