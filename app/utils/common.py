import base64

from app import model as m


def get_pretty_player(p: m.Player):
    return {
        'id': p.id, 'name': f'{p.name} {p.surname}',
        'img': base64.b64encode(p.img).decode("utf-8") if p.img else None
    }


def get_pretty_team(team: m.Team):
    recent_militancy = max(team.militancy, key=lambda mi: mi.year)
    league = recent_militancy.league
    return {
        'id': team.id, 'name': team.name,
        'img': base64.b64encode(team.img).decode("utf-8") if team.img else None,
        'league_id': league.id, 'league_name': league.display_name
    }


def get_pretty_league(league: m.League):
    return {
        'id': league.id, 'name': league.display_name,
        'img': base64.b64encode(league.img).decode("utf-8") if league.img else None,
        'country_code': league.country_code
    }
