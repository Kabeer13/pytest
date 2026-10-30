import pytest

@pytest.mark.django_db
def test_pokemon_endpoint_rejects_post(client):
    assert client.post("/api/pokemon/pikachu/").status_code == 405

@pytest.mark.django_db
def test_pokemon_endpoint_rejects_put(client):
    assert client.put("/api/pokemon/pikachu/").status_code == 405
