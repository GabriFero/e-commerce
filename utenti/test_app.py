import pytest
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    # Ricrea il database prima di ogni test
    with app.app_context():
        db.create_all()

    yield client

def test_get_users(client):
    # Test GET /users
    response = client.get('/users')
    assert response.status_code == 200
    assert response.json is not None

def test_get_user(client):
    # Test GET /users/<user_id>
    response = client.get('/users/1')
    assert response.status_code == 404  # Assumendo che l'utente con ID 1 non esista

def test_add_user(client):
    # Test POST /users
    data = {
        "nome": "Mario",
        "cognome": "Rossi",
        "codice_fiscale": "RSSMRA80A01H501Z",
        "indirizzo": "Via Roma 123",
        "email": "mario.rossi@example.com",
        "numero_telefono": "123456789"
    }

    response = client.post('/users', json=data)
    assert response.status_code == 201
    assert response.json is not None

def test_update_user(client):
    # Test PUT /users/<user_id>
    data = {
        "indirizzo": "Nuovo indirizzo",
        "numero_telefono": "987654321"
    }

    response = client.put('/users/1', json=data)
    assert response.status_code == 404  # Assumendo che l'utente con ID 1 non esista

def test_delete_user(client):
    # Test DELETE /users/<user_id>
    response = client.delete('/users/1')
    assert response.status_code == 404  # Assumendo che l'utente con ID 1 non esista
