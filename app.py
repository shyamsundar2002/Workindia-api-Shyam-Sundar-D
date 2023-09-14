from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import random

app = Flask(__name__)

# Database configuration (you can replace this with your MySQL configuration)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-actual-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(10), default='guest')

# Match model
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_1 = db.Column(db.String(80), nullable=False)
    team_2 = db.Column(db.String(80), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='upcoming')

    # Relationship between Match and Team
    teams = db.relationship('Team', backref='match', lazy=True)

# Team model
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)

    # Relationship between Team and Player
    players = db.relationship('Player', backref='team', lazy=True)

# Player model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    matches_played = db.Column(db.Integer, nullable=True)
    runs = db.Column(db.Integer, nullable=True)
    average = db.Column(db.Float, nullable=True)
    strike_rate = db.Column(db.Float, nullable=True)

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

# Squad model (for team-squad relationship)
class Squad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

# Registration endpoint
@app.route('/api/admin/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']
    email = data['email']
    
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'status': 'Username or email already exists', 'status_code': 400}), 400
    
    new_user = User(username=username, password=password, email=email, role='admin')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'status': 'Admin Account successfully created', 'status_code': 200, 'user_id': new_user.id})

# Login endpoint
@app.route('/api/admin/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.password == password:
        access_token = create_access_token(identity=user.id)
        return jsonify({'status': 'Login successful', 'status_code': 200, 'user_id': user.id, 'access_token': access_token})
    
    return jsonify({'status': 'Incorrect username/password provided. Please retry', 'status_code': 401}), 401

# Create Match endpoint
@app.route('/api/matches', methods=['POST'])
@jwt_required()
def create_match():
    data = request.get_json()
    team_1 = data['team_1']
    team_2 = data['team_2']
    date = datetime.strptime(data['date'], '%Y-%m-%d')
    venue = data['venue']
    
    match = Match(team_1=team_1, team_2=team_2, date=date, venue=venue)
    db.session.add(match)
    db.session.commit()
    
    return jsonify({'message': 'Match created successfully', 'match_id': match.id})

# Get Matches endpoint
@app.route('/api/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    match_list = [{'match_id': match.id, 'team_1': match.team_1, 'team_2': match.team_2, 'date': match.date.strftime('%Y-%m-%d'), 'venue': match.venue} for match in matches]
    
    return jsonify({'matches': match_list})

# Get Match Details endpoint
@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'message': 'Match not found'}), 404
    
    squads = {
        'team_1': [{'player_id': player.id, 'name': player.name} for player in match.teams[0].players],
        'team_2': [{'player_id': player.id, 'name': player.name} for player in match.teams[1].players]
    }
    
    match_details = {
        'match_id': match.id,
        'team_1': match.team_1,
        'team_2': match.team_2,
        'date': match.date.strftime('%Y-%m-%d'),
        'venue': match.venue,
        'status': match.status,
        'squads': squads
    }
    
    return jsonify(match_details)

# Add Player to Squad endpoint (admin only)
@app.route('/api/teams/<int:team_id>/squad', methods=['POST'])
@jwt_required()
def add_player_to_squad(team_id):
    data = request.get_json()
    name = data['name']
    role = data['role']
    matches_played = random.randint(10,100)
    runs=random.randint(100,1000)
    average=random.random()*100
    strike_rate=random.random()*100
    
    player = Player(name=name, role=role,matches_played=matches_played, runs=runs, average=average, strike_rate=strike_rate, team_id=team_id)
    db.session.add(player)
    db.session.commit()
    
    return jsonify({'message': 'Player added to squad successfully', 'player_id': player.id})

# Get Player Statistics endpoint (admin only)
@app.route('/api/players/<int:player_id>/stats', methods=['GET'])
@jwt_required()
def get_player_statistics(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'message': 'Player not found'}), 404
    
    # Replace this with actual player statistics retrieval logic
    player_statistics = {'player_id': player.id, 'name': player.name, 'role': player.role, 'matches_played': player.matches_played, 'runs': player.runs , 'average': player.average, 'strike_rate': player.strike_rate}
    
    return jsonify(player_statistics)



# Create Team for a Match endpoint (admin only)
@app.route('/api/matches/<int:match_id>/teams', methods=['POST'])
@jwt_required()
def create_team(match_id):
    data = request.get_json()
    team_name = data.get('team_name')
    player_list = data.get('players', [])
    
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'message': 'Match not found'}), 404
    
    if not team_name:
        return jsonify({'message': 'Team name is required'}), 400
    
    team = Team(name=team_name, match_id=match_id)
    db.session.add(team)
    
    for player_data in player_list:
        player_name = player_data.get('name')
        player_role = player_data.get('role')
        if player_name and player_role:
            player = Player(name=player_name, role=player_role, team=team)
            db.session.add(player)
    
    db.session.commit()
    
    return jsonify({'message': 'Team and players created successfully', 'team_id': team.id})




if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)