import pytest
from django.test import Client

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def sample_pokemon():
    return {"id": 25, "name": "Pikachu", "height": 4, "weight": 60,
            "image": "https://example.com/pikachu.png", "types": ["electric"],
            "abilities": ["static"], "stats": [{"name": "speed", "value": 90}]}
