import pytest

from app import validators as v


@pytest.mark.parametrize(
    "value,ok",
    [
        ("María José", True),
        ("Ana", True),
        ("a" * 30, True),
        ("a" * 31, False),
        ("Maria123", False),
        ("Ana  Maria", False),
        (" Ana", False),
        ("Ana ", False),
        ("Ana-Maria", False),
        ("", False),
    ],
)
def test_nombres(value, ok):
    assert v.is_valid_nombres(value) is ok


@pytest.mark.parametrize(
    "value,ok",
    [("Quispe", True), ("a" * 20, True), ("a" * 21, False), ("Quispe9", False), ("De La", False)],
)
def test_apellido(value, ok):
    assert v.is_valid_apellido(value) is ok


@pytest.mark.parametrize(
    "value,ok",
    [
        ("juan_perez", True),
        ("a" * 20, True),
        ("a" * 21, False),
        ("1234", False),
        ("ab cd", False),
        ("j.perez-1!", True),
        ("", False),
    ],
)
def test_usuario(value, ok):
    assert v.is_valid_usuario(value) is ok


@pytest.mark.parametrize(
    "value,ok",
    [
        ("a" * 9, False),
        ("a" * 10, True),
        ("Clave#12345", True),
        ("a" * 64, True),
        ("a" * 65, False),
        ("con espacio1", False),
    ],
)
def test_password(value, ok):
    assert v.is_valid_password(value) is ok


@pytest.mark.parametrize(
    "value,ok",
    [("ana@example.com", True), ("ana@@example", False), ("ana@example", False), ("ana.com", False)],
)
def test_email(value, ok):
    assert v.is_valid_email(value) is ok


@pytest.mark.parametrize(
    "value,ok",
    [
        ("912345678", True),
        ("812345678", False),
        ("91234567", False),
        ("9123456789", False),
        ("+51912345678", False),
    ],
)
def test_phone(value, ok):
    assert v.is_valid_phone(value) is ok
