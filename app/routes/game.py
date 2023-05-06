import base64
import logging
import typing as t

from flask import jsonify, request, abort, Blueprint

from app import model as m
from app.routes import game_utils

bp = Blueprint('game', __name__)
logger = logging.getLogger()


@bp.route('/api/game/challenge', methods=['GET'])
def challenge():
    result = game_utils.generate_challenge()
    if not result:
        abort(500)

    ret = [
        {
            'id': p.id, 'name': f'{p.name} {p.surname}',
            'img': base64.b64encode(p.img).decode("utf-8") if p.img else None
        }
        for i, p in enumerate(result)
    ]

    return jsonify(ret)
