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
    return os.getenv('MINIMUM_PLAYER_VALUE', 20)


def get_random_players_n_to_choose_from():
    return os.getenv('RANDOM_PLAYERS_N', 100)


def get_maximum_path_length():
    return os.getenv('MAXIMUM_PATH_LENGTH', 6)
