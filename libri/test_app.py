import pytest
from app import app, db_books, Book

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    # Ricrea il database prima di ogni test
    with app.app_context():
        db_books.create_all()

    yield client

def test_get_books(client):
    # Test GET /books
    response = client.get('/books')
    assert response.status_code == 200
    assert response.json is not None

def test_add_book(client):
    # Test POST /books
    data = {
        "isbn": "1234567890123",
        "title": "Test Book",
        "author": "Test Author",
        "publication_year": 2022,
        "genre": "Test Genre",
        "num_pages": 200,
        "price": 19.99
    }

    response = client.post('/books', json=data)
    assert response.status_code == 201
    assert response.json is not None

def test_update_book(client):
    # Test PUT /books/<isbn>
    data = {
        "title": "Updated Test Book",
        "author": "Updated Test Author"
    }

    response = client.put('/books/1234567890123', json=data)
    assert response.status_code == 200
    assert response.json is not None

def test_delete_book(client):
    # Test DELETE /books/<isbn>
    response = client.delete('/books/1234567890123')
    assert response.status_code == 200
    assert response.json is not None

def test_get_book_by_isbn(client):
    # Test GET /book/<isbn>
    response = client.get('/book/1234567890123')
    assert response.status_code == 200
    assert response.json is not None

def test_get_nonexistent_book_by_isbn(client):
    # Test GET /book/<isbn> when book does not exist
    response = client.get('/book/invalid_isbn')
    assert response.status_code == 404
    assert response.json is not None
