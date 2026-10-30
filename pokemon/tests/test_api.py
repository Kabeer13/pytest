from unittest.mock import patch
import pytest
from pokemon.services import PokemonAPIError

@pytest.mark.django_db
@patch("pokemon.views.fetch_pokemon")
def test_pokemon_endpoint_success(mock_fetch, client, sample_pokemon):
    mock_fetch.return_value = sample_pokemon
    response = client.get("/api/pokemon/pikachu/")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["pokemon"]["name"] == "Pikachu"

@pytest.mark.django_db
@patch("pokemon.views.fetch_pokemon")
@pytest.mark.parametrize("lookup", ["013", "13", "weedle"])
def test_pokemon_endpoint_passes_lookup_to_service(mock_fetch, client, sample_pokemon, lookup):
    mock_fetch.return_value = sample_pokemon
    response = client.get(f"/api/pokemon/{lookup}/")
    assert response.status_code == 200
    mock_fetch.assert_called_once_with(lookup)

@pytest.mark.django_db
@patch("pokemon.views.fetch_pokemon")
def test_pokemon_endpoint_not_found(mock_fetch, client):
    mock_fetch.side_effect = ValueError("No Pokémon found.")
    response = client.get("/api/pokemon/unknown/")
    assert response.status_code == 404
    assert response.json()["ok"] is False

@pytest.mark.django_db
@patch("pokemon.views.fetch_pokemon")
def test_pokemon_endpoint_upstream_failure(mock_fetch, client):
    mock_fetch.side_effect = PokemonAPIError("Upstream unavailable.")
    response = client.get("/api/pokemon/pikachu/")
    assert response.status_code == 502

@pytest.mark.django_db
def test_pages_load(client):
    for url in ["/", "/learn/", "/lab/", "/coverage/"]:
        assert client.get(url).status_code == 200
