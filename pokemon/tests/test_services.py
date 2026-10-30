from unittest.mock import Mock, patch
import pytest
import requests
from pokemon.services import fetch_pokemon, PokemonAPIError

@pytest.fixture
def pokeapi_payload():
    return {"id": 13, "name": "weedle", "height": 3, "weight": 32,
            "sprites": {"other": {"official-artwork": {"front_default": "https://img.test/weedle.png"}},
                        "front_default": "https://img.test/fallback.png"},
            "types": [{"type": {"name": "bug"}}, {"type": {"name": "poison"}}],
            "abilities": [{"ability": {"name": "shield-dust"}}],
            "stats": [{"stat": {"name": "speed"}, "base_stat": 50}]}

@patch("pokemon.services.requests.get")
def test_fetch_pokemon_success(mock_get, pokeapi_payload):
    response = Mock(status_code=200)
    response.json.return_value = pokeapi_payload
    mock_get.return_value = response
    result = fetch_pokemon("weedle")
    assert result["name"] == "Weedle"
    assert result["types"] == ["bug", "poison"]
    mock_get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/weedle", timeout=8)

@patch("pokemon.services.requests.get")
@pytest.mark.parametrize("pokemon_id", ["13", "#013", "  #13  "])
def test_fetch_pokemon_accepts_pokedex_number(mock_get, pokeapi_payload, pokemon_id):
    response = Mock(status_code=200)
    response.json.return_value = pokeapi_payload
    mock_get.return_value = response
    result = fetch_pokemon(pokemon_id)
    assert result["id"] == 13
    mock_get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/13", timeout=8)

@patch("pokemon.services.requests.get")
def test_fetch_pokemon_not_found(mock_get):
    mock_get.return_value = Mock(status_code=404)
    with pytest.raises(ValueError, match="was not found"):
        fetch_pokemon("missingno")

@patch("pokemon.services.requests.get")
def test_fetch_pokemon_network_error(mock_get):
    mock_get.side_effect = requests.Timeout()
    with pytest.raises(PokemonAPIError, match="Could not connect"):
        fetch_pokemon("pikachu")

@patch("pokemon.services.requests.get")
def test_fetch_pokemon_upstream_error(mock_get):
    mock_get.return_value = Mock(status_code=503)
    with pytest.raises(PokemonAPIError, match="temporarily unavailable"):
        fetch_pokemon("pikachu")

@patch("pokemon.services.requests.get")
def test_fetch_pokemon_invalid_json_shape(mock_get):
    response = Mock(status_code=200)
    response.json.return_value = {"name": "pikachu"}
    mock_get.return_value = response
    with pytest.raises(PokemonAPIError, match="unexpected format"):
        fetch_pokemon("pikachu")

def test_fetch_pokemon_empty_name_does_not_call_api():
    with patch("pokemon.services.requests.get") as mock_get:
        with pytest.raises(ValueError, match="Enter a Pokémon name"):
            fetch_pokemon("   ")
        mock_get.assert_not_called()
