from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(engine_options={
    'pool_pre_ping': True,
    'max_overflow': 200,
    'pool_timeout': 60.0
})


class TeamMilitancy(db.Model):
    __tablename__ = 'teammilitancy'
    __table_args__ = (
        db.PrimaryKeyConstraint('team_id', 'league_id', 'year'),
    )
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))
    year = db.Column(db.Integer)


class Team(db.Model):
    __tablename__ = 'team'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    img = db.Column(db.LargeBinary)
    img_url = db.Column(db.String)
    militancy = db.relationship(TeamMilitancy, backref='team')


class Militancy(db.Model):
    __tablename__ = 'militancy'
    __table_args__ = (
        db.PrimaryKeyConstraint('player_id', 'team_id', 'year'),
    )

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer)
    start_date = db.Column(db.Date, default=None)
    end_date = db.Column(db.Date, default=None)
    appearences = db.Column(db.Integer)
    team = db.relationship(Team, backref='player_militancy')


class Player(db.Model):
    __tablename__ = 'player'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    surname = db.Column(db.String)
    img = db.Column(db.LargeBinary)
    img_url = db.Column(db.String)
    value = db.Column(db.Float, default=0)
    militancy = db.relationship(Militancy, backref='player')


class League(db.Model):
    __tablename__ = 'league'

    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String)
    img = db.Column(db.LargeBinary)
    img_url = db.Column(db.String)
    country_code = db.Column(db.String)
    militancy = db.relationship(TeamMilitancy, backref='league')


class LeagueSeasons(db.Model):
    __tablename__ = 'leagueseasons'
    __table_args__ = (
        db.PrimaryKeyConstraint('league_id', 'year'),
    )

    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))
    year = db.Column(db.Integer)
    start_date = db.Column(db.Date, default=None)
    end_date = db.Column(db.Date, default=None)
