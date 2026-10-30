import pytest
from pokemon.utils import format_pokemon_name

@pytest.mark.parametrize(("value", "expected"), [
    ("pikachu", "Pikachu"), ("  mr mime  ", "Mr Mime"), ("", ""),
])
def test_display_name_normalization(value, expected):
    assert format_pokemon_name(value) == expected

def test_display_name_rejects_non_string():
    with pytest.raises(AttributeError):
        format_pokemon_name(None)
