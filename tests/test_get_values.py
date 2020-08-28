import pytest

from pytest_pyppeteer.models import Pyppeteer


@pytest.mark.parametrize("target", ["target1"], indirect=True)
async def test_get_values(target: Pyppeteer):
    weekly_reputation_movies = await target.get_values("weekly_reputation_list")
    print(weekly_reputation_movies)
    assert weekly_reputation_movies
