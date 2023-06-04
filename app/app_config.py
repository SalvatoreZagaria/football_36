import os
import logging


AFFIRMATIVES = {'yes', 'True', 'true', '1', 't', 'T', 'y', 'Y', 'on', 'ON'}

logger = logging.getLogger()


def get_database_url():
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_addr = os.getenv('DB_ADDRESS', 'localhost')
    db_port = os.getenv('DB_PORT', 5432)
    db_name = os.getenv('DB_NAME', 'football')
    if not all((db_user, db_password, db_addr, db_port, db_name)):
        raise EnvironmentError('DB env variables unset')

    url = f'postgresql://{db_user}:{db_password}@{db_addr}:{db_port}/{db_name}'
    logger.info(f'connecting to database: postgresql://*****:*****@{db_addr}:{db_port}/{db_name}')

    return url


def get_neo4j_uri():
    return os.getenv('NEO4J_URI', 'bolt://localhost:7687')


def get_neo4j_user():
    return os.getenv('NEO4J_USER')


def get_neo4j_password():
    return os.getenv('NEO4J_PASSWORD')


def get_minimum_player_value():
    return int(os.getenv('MINIMUM_PLAYER_VALUE', 50))


def get_minimum_player_value_with_leagues_filter():
    return int(os.getenv('MINIMUM_PLAYER_VALUE_LEAGUES_FILTER', 20))


def players_selection_limit():
    return int(os.getenv('PLAYERS_SELECTION_LIMIT', 300))


def get_maximum_path_length():
    return int(os.getenv('MAXIMUM_PATH_LENGTH', 6))
