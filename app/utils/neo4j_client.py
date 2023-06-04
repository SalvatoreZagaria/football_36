import typing as t
import traceback
import logging

from neo4j import GraphDatabase

from app import app_config

driver = GraphDatabase.driver(app_config.get_neo4j_uri(),
                              auth=(app_config.get_neo4j_user(), app_config.get_neo4j_password()))
driver.verify_connectivity()


logger = logging.getLogger()


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
        f'path = shortestPath((start)-[:PLAYED_WITH*..{max_len}]-(end))' +
        """RETURN path IS NOT NULL AND length(path) > $min_len
        """, start_id=str(player_id_1), end_id=str(player_id_2), min_len=min_len
    )

    return records[0][0]


def have_played_together(player_id_1: t.Union[str, int], player_id_2: t.Union[str, int]) -> bool:
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


def get_relationship(player_id_1: t.Union[str, int], player_id_2: t.Union[str, int]) -> t.Optional[t.Dict[str, int]]:
    records, _, _ = driver.execute_query(
        """
        MATCH
        (start:Player {playerId: $start_id}),
        (end:Player {playerId: $end_id}),
        (start)-[r:PLAYED_WITH]-(end)
        RETURN
          r
        LIMIT 1
        """, start_id=str(player_id_1), end_id=str(player_id_2)
    )
    if not records:
        return None

    try:
        return {
            'start': int(player_id_1),
            'team': int(records[0][0]._properties['team_id']),
            'end': int(player_id_2)
        }
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.error(f'Error while getting relationship -> {e}', extra={
            'start': player_id_1, 'end': player_id_2, 'stacktrace': stack_trace
        })
        return None


def shortest_path(player_id_1: t.Union[str, int], player_id_2: t.Union[str, int], limit: int = 10
                  ) -> t.Optional[t.List]:
    records, _, _ = driver.execute_query(
        """
        MATCH
          (start:Player {playerId: $start_id}),
          (end:Player {playerId: $end_id}),
          path = allShortestPaths((start)-[:PLAYED_WITH*..6]-(end))
        WHERE length(path) > 2
        RETURN path, reduce(weight = 0.0, n IN nodes(path) | weight + n.value) as weight
        ORDER BY length(path) ASC, weight DESC LIMIT $limit
        """, start_id=str(player_id_1), end_id=str(player_id_2), limit=limit
    )

    return records or None
