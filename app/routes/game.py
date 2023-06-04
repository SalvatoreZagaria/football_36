import logging

from flask import jsonify, request, abort, Blueprint

from app import model as m
from app.routes import game_utils
from app.utils import neo4j_client, common

bp = Blueprint('game', __name__)
logger = logging.getLogger()


@bp.route('/api/game/challenge', methods=['GET'])
def challenge():
    leagues_filter = request.args.getlist('leagues')
    try:
        leagues_filter = [int(i) for i in leagues_filter]
    except ValueError:
        abort(400)
    result = game_utils.generate_challenge(leagues_filter=leagues_filter)
    if not result:
        abort(500)

    ret = [
        common.get_pretty_player(p)
        for p in result
    ]

    return jsonify(ret)


@bp.route('/api/game/challenge/validate', methods=['POST'])
def validate_solution():
    node_ids = request.get_json(silent=True)
    if node_ids is None:
        abort(400)
    if not isinstance(node_ids, list):
        abort(400)
    if not all((isinstance(n, int) or isinstance(n, str) for n in node_ids)):
        abort(400)

    node_ids = [int(n) for n in node_ids]
    if len(set(node_ids)) != len(node_ids):
        abort(400)

    degrees = len(node_ids) - 2
    response = {'valid': True, 'error': None, 'submitted_solution_degrees': degrees}
    if not 0 < degrees < game_utils.MAXIMUM_PATH_LENGTH:
        response['valid'] = False
        response['error'] = 'Exceeded degrees'
        return jsonify(response)

    players = {p.id: p for p in m.db.session.query(m.Player).filter(m.Player.id.in_(node_ids)).all()}
    if len(node_ids) != len(players):
        logger.error('Players not found in SQL DB', extra={'players': node_ids})
        abort(400)

    # checking submitted solution
    submitted_path = []
    for i in range(len(node_ids) - 1):
        first_node = node_ids[i]
        second_node = node_ids[i + 1]
        relationship = neo4j_client.get_relationship(first_node, second_node)
        if not relationship:
            response['valid'] = False
            p1 = players[first_node]
            p2 = players[second_node]
            response['error'] = f'{p1.name} {p1.surname} and {p2.name} {p2.surname} have not played together in the last 3 years'
            response['players_affected'] = [common.get_pretty_player(p) for p in (p1, p2)]
            return jsonify(response)

        submitted_path.append(relationship)

    team_ids = list({r['team'] for r in submitted_path})
    teams = {team.id: team for team in m.db.session.query(m.Team).filter(m.Team.id.in_(team_ids)).all()}
    if len(team_ids) != len(teams):
        logger.error('Teams not found in SQL DB', extra={'teams': team_ids})
        abort(500)

    # retrieving full info of the solution's entities
    response['submitted_solution'] = [
        {
            'start': common.get_pretty_player(players[rel['start']]),
            'team': common.get_pretty_team(teams[rel['team']]),
            'end': common.get_pretty_player(players[rel['end']])
        }
        for rel in submitted_path
    ]

    # checking if solution is optimal
    optimal_path = game_utils.get_optimal_path(node_ids[0], node_ids[-1])
    if optimal_path is None:
        logger.error('Error while getting shortest path', extra={'node_ids': node_ids})
        abort(500)

    if len(response['submitted_solution']) == len(optimal_path):
        response['is_optimal'] = True
        return jsonify(response)
    response['is_optimal'] = False

    players_to_query = []
    teams_to_query = []
    for rel in optimal_path:
        for key in ('start', 'end'):
            if rel[key] not in players:
                players_to_query.append(rel[key])
        if rel['team'] not in teams:
            teams_to_query.append(rel['team'])

    players.update(
        {p.id: p for p in m.db.session.query(m.Player).filter(m.Player.id.in_(players_to_query)).all()}
    )
    teams.update(
        {team.id: team for team in m.db.session.query(m.Team).filter(m.Team.id.in_(teams_to_query)).all()}
    )

    response['optimal_solution'] = [
        {
            'start': common.get_pretty_player(players[rel['start']]),
            'team': common.get_pretty_team(teams[rel['team']]),
            'end': common.get_pretty_player(players[rel['end']])
        }
        for rel in optimal_path
    ]
    response['optimal_solution_degrees'] = len(optimal_path) - 2

    return jsonify(response)


@bp.route('/api/game/hint', methods=['POST'])
def hint():
    body = request.get_json(silent=True)
    if not (body and isinstance(body, dict)):
        abort(400)
    hint_type = body.get('type')
    if hint_type == 'player_team':
        player_id = body.get('player_id')
        if not player_id:
            abort(400)
        player = m.db.session.query(m.Player).get(player_id)
        if not player:
            abort(400)
        militancy = max(player.militancy, key=lambda mi: mi.start_date)
        return jsonify(common.get_pretty_team(militancy.team))
    else:
        abort(400)
