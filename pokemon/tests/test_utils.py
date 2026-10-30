import pytest
from pokemon.utils import format_pokemon_name

@pytest.mark.parametrize(("raw", "expected"), [
    ("pikachu", "Pikachu"), ("mr-mime", "Mr-Mime"),
    ("  charizard  ", "Charizard"), ("", ""),
])
def test_format_pokemon_name(raw, expected):
    assert format_pokemon_name(raw) == expected
