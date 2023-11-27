from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import os
import pika
import json
import logging
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@flask_db2:5432/Books'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_books = SQLAlchemy(app)

log_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s')
log_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(log_formatter)
app.logger.addHandler(log_handler)

class Book(db_books.Model):
    __tablename__ = 'books'

    isbn = db_books.Column(db_books.String(13), primary_key=True)
    title = db_books.Column(db_books.String(100), nullable=False)
    author = db_books.Column(db_books.String(100), nullable=False)
    publication_year = db_books.Column(db_books.Integer, nullable=True)
    genre = db_books.Column(db_books.String(50), nullable=True)
    num_pages = db_books.Column(db_books.Integer, nullable=True)
    price = db_books.Column(db_books.Float, nullable=True)

    def as_dict(self):
        return {
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publication_year': self.publication_year,
            'genre': self.genre,
            'num_pages': self.num_pages,
            'price': self.price
        }

db_books.create_all()

rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
rabbitmq_user = os.environ.get('RABBITMQ_USER', 'user')
rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'password')

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),heartbeat=600))
channel = connection.channel()

channel.queue_declare(queue='notifications')

@app.route('/books', methods=['GET'])
def get_books():
    try:
        books = Book.query.all()
        app.logger.info('Endpoint /books accessed. Returning book data.')
        return jsonify([book.as_dict() for book in books])
    except Exception as e:
        app.logger.error(f"Error in get_books: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/books', methods=['POST'])
def add_book():
    try:
        data = request.json
        new_book = Book(**data)
        db_books.session.add(new_book)
        db_books.session.commit()

        notification_data = {
            "event": "new_book_added",
            "book_data": new_book.as_dict()
        }

        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

        return jsonify(new_book.as_dict()), 201
    except Exception as e:
        db_books.session.rollback()
        return jsonify({"error": str(e)}), 500

# Endpoint per aggiornare un libro tramite ISBN
@app.route('/books/<isbn>', methods=['PUT'])
def update_book(isbn):
    book = Book.query.get(isbn)
    if book:
        data = request.json
        for key, value in data.items():
            setattr(book, key, value)
        db_books.session.commit()
        notification_data = {
            "event": "book_updated",
            "book_data": book.as_dict()
        }

        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

        return jsonify(book.as_dict())
    return jsonify({'message': 'Book not found'}), 404

# Endpoint per eliminare un libro tramite ISBN
@app.route('/books/<isbn>', methods=['DELETE'])
def delete_book(isbn):
    book = Book.query.get(isbn)
    if book:
        db_books.session.delete(book)
        db_books.session.commit()
        notification_data = {
            "event": "book_deleted",
            "book_data": book.as_dict()
        }

        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(notification_data))

        return jsonify({'message': 'Book deleted'})
    return jsonify({'message': 'Book not found'}), 404

@app.route('/book/<string:book_isbn>', methods=['GET'])
def get_book_by_isbn(book_isbn):
    book = Book.query.get(book_isbn)
    if book is None:
        return make_response(jsonify({'error': 'Libro non trovato'}), 404)
    else:
        return make_response(jsonify({'status': 'ok', 'book': book.as_dict()}), 200)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=7000)
    finally:
        if connection:
            connection.close()

