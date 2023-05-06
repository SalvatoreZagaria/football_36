import random

from neo4j import GraphDatabase

from app import app_config

driver = GraphDatabase.driver(app_config.get_neo4j_uri(),
                              auth=(app_config.get_neo4j_user(), app_config.get_neo4j_password()))
driver.verify_connectivity()


def validate_path_for_challenge_creation(player_id_1: int, player_id_2: int, max_len: int, min_len=2) -> bool:
    # checking if they have played together (if yes, there's no challenge
    if have_played_together(player_id_1, player_id_2):
        return False

    # checking if there's a path between the 2 of length between min and max len
    records, _, _ = driver.execute_query(
        """
        OPTIONAL MATCH
          (start:Player {playerId: $start_id}),
          (end:Player {playerId: $end_id}),""" +
          f'path = allShortestPaths((start)-[:PLAYED_WITH*..{max_len}]-(end))' +
        """WHERE length(path) > $min_len
        RETURN path IS NOT NULL
        LIMIT 1
        """, start_id=str(player_id_1), end_id=str(player_id_2), min_len=min_len
    )
    return records[0][0]


def have_played_together(player_id_1: int, player_id_2: int):
    records, _, _ = driver.execute_query(
        """
        MATCH
        (start:Player {playerId: $start_id}),
        (end:Player {playerId: $end_id})
        RETURN
          exists((start)-[:PLAYED_WITH]-(end)) AS have_played_together
        """, start_id=str(player_id_1), end_id=str(player_id_2)
    )
    return records[0][0]
