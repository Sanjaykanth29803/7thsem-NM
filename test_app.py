import pytest
from app import app, init_db, DB_PATH
import os
import sqlite3

# Setup a test database
TEST_DB = "test_vaccinations.db"

@pytest.fixture
def client():
    # Override the DB_PATH for testing
    app.config['TESTING'] = True
    app.config['DB_PATH'] = TEST_DB
    
    # Initialize a fresh test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()
    
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Test if home page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    # ✅ Update this line to match your home page title
    assert b"Vaccination" in response.data or b"Child" in response.data


def test_add_child(client):
    """Test adding a new child"""
    # ✅ Make sure the route matches your app.py route (commonly '/add')
    response = client.post('/add', data={
        'name': 'Test Child',
        'dob': '2020-01-01',
        'phone': '9999999999'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # ✅ Adjust message depending on your flash message or success text
    assert b"success" in response.data or b"added" in response.data

    # Verify in database
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE name = ?", ('Test Child',))
    child = cursor.fetchone()
    conn.close()
    assert child is not None


def test_vaccine_schedule(client):
    """Test vaccine schedule generation"""
    # ✅ Check route name — usually '/vaccine_schedule'
    response = client.get('/vaccine_schedule')
    assert response.status_code == 200
    assert b"Vaccine" in response.data or b"Schedule" in response.data

