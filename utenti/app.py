from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from os import environ
import psycopg2
import pika
import json
import os
import logging
from logging.handlers import RotatingFileHandler

rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
rabbitmq_user = os.environ.get('RABBITMQ_USER', 'user')
rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'password')

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),heartbeat=600))
channel = connection.channel()

# Definisci la coda delle notifiche
channel.queue_declare(queue='notifications')

app = Flask(__name__)

# Configurazione del nuovo database per gli utenti
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@flask_db:5432/Users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Per disabilitare le notifiche di modifica

import os

log_directory = 'logs'
log_file = f'{log_directory}/app.log'

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
log_file = 'logs/app.log'
handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

db = SQLAlchemy(app)

# Definizione del modello per la tabella degli utenti
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cognome = db.Column(db.String(50), nullable=False)
    codice_fiscale = db.Column(db.String(16), nullable=False, unique=True)
    indirizzo = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    numero_telefono = db.Column(db.String(15), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cognome': self.cognome,
            'codice_fiscale': self.codice_fiscale,
            'indirizzo': self.indirizzo,
            'email': self.email,
            'numero_telefono': self.numero_telefono
        }

# Creazione della tabella degli utenti nel nuovo database
db.create_all()

# Endpoint per ottenere tutti gli utenti
@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        response_data = [user.as_dict() for user in users]
        
        app.logger.info('Successfully retrieved all users')
        return jsonify(response_data)
    except Exception as e:
        app.logger.error('Failed to retrieve users: %s', e)
        return jsonify({"error": "Internal Server Error"}), 500



# Endpoint per ottenere un singolo utente tramite ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify(user.as_dict())
    return jsonify({'message': 'User not found'}), 404

# Endpoint per aggiungere un nuovo utente
@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    new_user = User(**data)
    db.session.add(new_user)
    db.session.commit()

    # Invia una notifica alla coda delle notifiche
    notification_data = {
            "event": "new_user_added",
            "user_data": new_user.as_dict()
        }

    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

    return jsonify(new_user.as_dict()), 201

# Endpoint per aggiornare un utente tramite ID
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.json
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        notification_data = {
            "event": "usere updated",
            "user_data": user.as_dict()
        }

        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

        return jsonify(user.as_dict())
    return jsonify({'message': 'User not found'}), 404

# Endpoint per eliminare un utente tramite ID
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        notification_data = {
            "event": "deleted user",
            "user_data": user.as_dict()
        }

        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

        return jsonify({'message': 'User deleted'})
    return jsonify({'message': 'User not found'}), 404

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user_id(user_id):
    user = User.query.get(user_id)
    if user is None:
        return make_response(jsonify({'error': 'Utente non trovato'}), 404)
    else:
        return make_response(jsonify({'status': 'ok', 'user': user.as_dict()}), 200)

if __name__ == '__main__':
    app.run(host='172.22.0.5')

