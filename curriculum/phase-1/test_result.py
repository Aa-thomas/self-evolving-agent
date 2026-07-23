import pytest

from result import Err, Ok


def test_unwrap_returns_the_ok_value():
    assert Ok("value").unwrap() == "value"


def test_unwrap_err_returns_the_err_value():
    assert Err("problem").unwrap_err() == "problem"


def test_unwrap_raises_for_an_err():
    with pytest.raises(ValueError, match=r"unwrap\(\) on an Err"):
        Err("problem").unwrap()


def test_unwrap_err_raises_for_an_ok():
    with pytest.raises(ValueError, match=r"unwrap_err\(\) on an Ok"):
        Ok("value").unwrap_err()
