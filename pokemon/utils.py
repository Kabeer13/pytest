def format_pokemon_name(name: str) -> str:
    """Normalize a Pokémon name for display."""
    return " ".join(part.capitalize() for part in name.strip().split())
