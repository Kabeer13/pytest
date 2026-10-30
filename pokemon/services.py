import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

class PokemonAPIError(Exception):
    """Raised when the upstream Pokémon API cannot provide valid data."""

def fetch_pokemon(name: str) -> dict:
    clean_name = name.strip().lower().lstrip("#").strip()
    if not clean_name:
        raise ValueError("Enter a Pokémon name.")
    if clean_name.isdigit():
        clean_name = str(int(clean_name))
    try:
        response = requests.get(f"{POKEAPI_BASE_URL}{clean_name}", timeout=8)
    except requests.RequestException as exc:
        raise PokemonAPIError("Could not connect to PokéAPI. Please try again.") from exc
    if response.status_code == 404:
        raise ValueError(f"No Pokémon named '{clean_name}' was found.")
    if response.status_code != 200:
        raise PokemonAPIError("PokéAPI is temporarily unavailable. Please try again.")
    try:
        raw = response.json()
        return {
            "id": raw["id"],
            "name": raw["name"].capitalize(),
            "height": raw["height"],
            "weight": raw["weight"],
            "image": raw["sprites"]["other"]["official-artwork"]["front_default"] or raw["sprites"]["front_default"],
            "types": [item["type"]["name"] for item in raw["types"]],
            "abilities": [item["ability"]["name"] for item in raw["abilities"]],
            "stats": [{"name": item["stat"]["name"], "value": item["base_stat"]} for item in raw["stats"]],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PokemonAPIError("PokéAPI returned data in an unexpected format.") from exc
