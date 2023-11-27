import pytest
from app import app, db, Prestito

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    # Ricrea il database prima di ogni test
    with app.app_context():
        db.create_all()

    yield client

def test_get_prestito(client):
    # Test GET /prestiti/<id_prestito>
    response = client.get('/prestiti/1')
    assert response.status_code == 404  # Assumendo che il prestito con ID 1 non esista

def test_add_prestito(client):
    # Test POST /prestiti
    data = {
        "isbn": "1234567890123",
        "id": 1,
        "data_inizio": "2023-01-01",
        "data_fine": "2023-01-10",
        "stato": "in prestito"
    }

    response = client.post('/prestiti', json=data)
    assert response.status_code == 201
    assert response.json is not None

def test_update_prestito(client):
    # Test PUT /prestiti/<id_prestito>
    data = {
        "data_inizio": "2023-01-02",
        "data_fine": "2023-01-15",
        "stato": "restituito"
    }

    response = client.put('/prestiti/1', json=data)
    assert response.status_code == 404  # Assumendo che il prestito con ID 1 non esista

def test_delete_prestito(client):
    # Test DELETE /prestiti/<id_prestito>
    response = client.delete('/prestiti/1')
    assert response.status_code == 404  # Assumendo che il prestito con ID 1 non esista
