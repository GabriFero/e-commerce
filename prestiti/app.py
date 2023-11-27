from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika
import requests
import socket
from urllib3.connection import HTTPConnection
from datetime import datetime
import os
import json

rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
rabbitmq_user = os.environ.get('RABBITMQ_USER', 'user')
rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'password')

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),heartbeat=600))
channel = connection.channel()

channel.queue_declare(queue='notifications')


app = Flask(__name__)

# Configurazione del database dei Prestiti (MariaDB)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://mariadb:mariadb@mariadb:3306/prestiti'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Abilita TCP keep-alive
HTTPConnection.default_socket_options = (
    HTTPConnection.default_socket_options +
    [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
     (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
     (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
     (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)]
)

# Definizione del modello per i prestiti
class Prestito(db.Model):
    __tablename__ = 'prestiti'
    id_prestito = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), nullable=False)
    id = db.Column(db.Integer, nullable=False)
    data_inizio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fine = db.Column(db.DateTime)
    stato = db.Column(db.String(50), default='in prestito')

    def as_dict(self):
        return {
            'id_prestito': self.id_prestito,
            'isbn': self.isbn,
            'id': self.id,
            'data_inizio': self.data_inizio,
            'data_fine': self.data_fine,
            'stato': self.stato
        }

db.create_all()

@app.route('/prestiti/<int:id_prestito>', methods=['GET'])
def get_prestito(id_prestito):
    prestito = Prestito.query.get(id_prestito)
    if not prestito:
        return jsonify({'error': 'Prestito non trovato'}), 404
    return jsonify(prestito.as_dict()), 200

from flask import request, jsonify
import requests

@app.route('/prestiti', methods=['POST'])
def create_prestito():
    data = request.get_json()

    # Estrai i dati dalla richiesta
    isbn = data.get('isbn')
    id_utente = data.get('id')
    data_inizio_str = data.get('data_inizio')
    data_fine_str = data.get('data_fine')
    stato = data.get('stato', 'in prestito')

    # Verifica che l'ID dell'utente esista nel servizio "users"
    user_response = requests.get(f'http://flask_app:4000/user/{id_utente}')
    if user_response.status_code != 200:
        return jsonify({'error': 'Utente non trovato'}), 404
    
    # Verifica che l'ISBN esista nel servizio "books"
    book_response = requests.get(f'http://flask_app2:5000/book/{isbn}')
    if book_response.status_code != 200:
        return jsonify({'error': 'ISBN non trovato'}), 404

    # Converti le stringhe di data in oggetti datetime
    data_inizio = datetime.strptime(data_inizio_str, '%Y-%m-%d')
    data_fine = datetime.strptime(data_fine_str, '%Y-%m-%d') if data_fine_str else None

    # Crea il prestito
    prestito = Prestito(isbn=isbn, id=id_utente, data_inizio=data_inizio, data_fine=data_fine, stato=stato)
    db.session.add(prestito)
    db.session.commit()

    # Invia una notifica alla coda delle notifiche
    notification_data = {
        "event": "new_borrow_added",
        "book_data": {
            "id_prestito": prestito.id_prestito,
            "isbn": prestito.isbn,
            "id": prestito.id,
            "data_inizio": prestito.data_inizio.strftime('%Y-%m-%d %H:%M:%S'),
            "data_fine": prestito.data_fine.strftime('%Y-%m-%d %H:%M:%S') if prestito.data_fine else None,
            "stato": prestito.stato
        }
    }

    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

    return jsonify(prestito.as_dict()), 201


@app.route('/prestiti/<int:id_prestito>', methods=['PUT'])
def update_prestito(id_prestito):
    prestito = Prestito.query.get(id_prestito)
    if not prestito:
        return jsonify({'error': 'Prestito non trovato'}), 404

    data = request.get_json()
    data_inizio_str = data.get('data_inizio')
    data_fine_str = data.get('data_fine')
    stato = data.get('stato', prestito.stato)

    data_inizio = datetime.strptime(data_inizio_str, '%Y-%m-%d') if data_inizio_str else None
    data_fine = datetime.strptime(data_fine_str, '%Y-%m-%d') if data_fine_str else None

    # Invia una notifica alla coda delle notifiche prima di aggiornare il prestito
    notification_data = {
        "event": "prestito_updated",
        "prestito_data": {
            "id_prestito": prestito.id_prestito,
            "isbn": prestito.isbn,
            "id": prestito.id,
            "data_inizio": prestito.data_inizio.strftime('%Y-%m-%d %H:%M:%S') if prestito.data_inizio else None,
            "data_fine": prestito.data_fine.strftime('%Y-%m-%d %H:%M:%S') if prestito.data_fine else None,
            "stato": prestito.stato
        }
    }
    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

    prestito.data_inizio = data_inizio
    prestito.data_fine = data_fine
    prestito.stato = stato

    db.session.commit()

    return jsonify(prestito.as_dict())

@app.route('/prestiti/<int:id_prestito>', methods=['DELETE'])
def delete_prestito(id_prestito):
    prestito = Prestito.query.get(id_prestito)
    if not prestito:
        return jsonify({'error': 'Prestito non trovato'}), 404

    # Invia una notifica alla coda delle notifiche prima di eliminare il prestito
    notification_data = {
        "event": "prestito_deleted",
        "prestito_data": prestito.as_dict()
    }
    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

    # Elimina il prestito dal database
    db.session.delete(prestito)
    db.session.commit()

    return jsonify({'message': 'Prestito eliminato con successo'})

    
if __name__ == '__main__':
    app.run(host='172.22.0.7')