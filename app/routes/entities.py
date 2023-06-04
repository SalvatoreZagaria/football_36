import logging

import sqlalchemy
from sqlalchemy import func, select, text, tuple_, nullslast
from flask import jsonify, abort, Blueprint, request
from unidecode import unidecode

from app import model as m
from app.utils import common

bp = Blueprint('players', __name__)
logger = logging.getLogger()


@bp.route('/api/entities/player/<player_id>', methods=['GET'])
def get_player(player_id: int):
    player = m.db.session.query(m.Player).get(player_id)
    if not player:
        abort(404)

    return jsonify(common.get_pretty_player(player))


@bp.route('/api/entities/player/search/<query>', methods=['GET'])
def player_search(query: str):
    if len(query) < 3:
        return jsonify([])

    query = unidecode(query)
    players = m.db.session.query(m.Player).order_by(m.Player.value.desc()).filter(
        sqlalchemy.func.concat(m.Player.surname, ' ', m.Player.name).like(f'%{query}%')).limit(5).all()

    return jsonify([
        common.get_pretty_player(p) for p in players
    ])


@bp.route('/api/entities/league/search/<query>', methods=['GET'])
def league_search(query: str):
    if len(query) < 3:
        return jsonify([])

    query = unidecode(query)

    leagues = select(m.League.id).filter(m.League.display_name.ilike(f'{query}%')).cte('leagues')
    teammilitancies = select(m.TeamMilitancy).filter(
        tuple_(m.TeamMilitancy.league_id, m.TeamMilitancy.year).in_(
            select(m.TeamMilitancy.league_id, func.max(m.TeamMilitancy.year).label('max_year')).filter(
                m.TeamMilitancy.league_id.in_(leagues)).group_by(m.TeamMilitancy.league_id)
        )).cte('teammilitancies')
    teams = select(m.Team.id).filter(m.Team.id.in_(select(teammilitancies.c.team_id)))
    militancies = select(m.Militancy).filter(
        tuple_(m.Militancy.team_id, m.Militancy.year).in_(
            select(m.Militancy.team_id, func.max(m.Militancy.year).label('max_year')).filter(
                m.Militancy.team_id.in_(teams)).group_by(m.Militancy.team_id))).cte('militancies')
    teams_by_value = select(teams.columns.id.label('team_id'), func.sum(m.Player.value).label('team_value')
                            ).join(militancies, teams.c.id == militancies.c.team_id, isouter=True
                                   ).join(m.Player, militancies.c.player_id == m.Player.id, isouter=True
                                          ).group_by(teams.c.id).cte('teams_by_value')
    leagues_by_value = select(m.League.id, func.sum(teams_by_value.c.team_value).label('league_value')
                              ).join(teammilitancies, m.League.id == teammilitancies.c.league_id, isouter=True
                                     ).join(teams_by_value, teammilitancies.c.team_id == teams_by_value.c.team_id,
                                            isouter=True).group_by(m.League.id).order_by(
        nullslast(text('league_value DESC'))).limit(5).cte('leagues_by_value')

    res = m.db.session.query(m.League).filter(m.League.id.in_(select(leagues_by_value.c.id))).all()

    return jsonify([
        common.get_pretty_league(r) for r in res
    ])


@bp.route('/api/entities/team/search/<query>', methods=['GET'])
def team_search(query: str):
    if len(query) < 3:
        return jsonify([])

    query = unidecode(query)

    teams = select(m.Team.id).filter(m.Team.name.ilike(f'{query}%')).cte('teams')
    militancies = select(m.Militancy).filter(
        tuple_(m.Militancy.team_id, m.Militancy.year).in_(
            select(m.Militancy.team_id, func.max(m.Militancy.year).label('max_year')).filter(
                m.Militancy.team_id.in_(teams)).group_by(m.Militancy.team_id)
        )).cte('militancies')
    teams_by_value = select(teams.columns.id, func.sum(m.Player.value).label('team_value')
                            ).join(militancies, teams.c.id == militancies.c.team_id, isouter=True
                                   ).join(m.Player, militancies.c.player_id == m.Player.id, isouter=True
                                          ).group_by(teams.c.id).order_by(nullslast(text('team_value DESC'))
                                                                          ).limit(5).cte('teams_by_value')
    res = m.db.session.query(m.Team).filter(m.Team.id.in_(select(teams_by_value.c.id))).all()

    return jsonify([
        common.get_pretty_team(r) for r in res
    ])


@bp.route('/api/entities/league/top-leagues', methods=['GET'])
def top_leagues():
    page_number = page_size = None
    try:
        page_number = int(request.args.get('page_n', 1))
        page_size = int(request.args.get('page_size', 20))
    except:
        abort(400)

    offset = (page_number - 1) * page_size
    teammilitancies = select(m.TeamMilitancy).filter(
        tuple_(m.TeamMilitancy.league_id, m.TeamMilitancy.year).in_(
            select(m.TeamMilitancy.league_id, func.max(m.TeamMilitancy.year).label('max_year')
                   ).group_by(m.TeamMilitancy.league_id))).cte('teammilitancies')
    teams = select(m.Team.id).filter(m.Team.id.in_(select(teammilitancies.c.team_id)))
    militancies = select(m.Militancy).filter(
        tuple_(m.Militancy.team_id, m.Militancy.year).in_(
            select(m.Militancy.team_id, func.max(m.Militancy.year).label('max_year')).filter(
                m.Militancy.team_id.in_(teams)).group_by(m.Militancy.team_id))).cte('militancies')
    teams_by_value = select(teams.columns.id.label('team_id'), func.sum(m.Player.value).label('team_value')
                            ).join(militancies, teams.c.id == militancies.c.team_id, isouter=True
                                   ).join(m.Player, militancies.c.player_id == m.Player.id, isouter=True
                                          ).group_by(teams.c.id).cte('teams_by_value')
    leagues_by_value = select(m.League.id, func.sum(teams_by_value.c.team_value).label('league_value')
                              ).join(teammilitancies, m.League.id == teammilitancies.c.league_id, isouter=True
                                     ).join(teams_by_value, teammilitancies.c.team_id == teams_by_value.c.team_id,
                                            isouter=True).group_by(m.League.id).order_by(
        nullslast(text('league_value DESC'))).offset(offset).limit(page_size).cte('leagues_by_value')

    res = m.db.session.query(m.League).filter(m.League.id.in_(select(leagues_by_value.c.id))).all()

    return jsonify([
        common.get_pretty_league(r) for r in res
    ])
