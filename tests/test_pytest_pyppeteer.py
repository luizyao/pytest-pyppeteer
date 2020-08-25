import asyncio
from functools import partial

import pytest
from pytest_pyppeteer.models import Pyppeteer


async def query_rating(target: Pyppeteer, movie_or_book_name: str):
    await target.input("search_input", text=movie_or_book_name)
    await target.click("search_apply")

    # Into search results page
    target.switch_page("SearchResultsPage")
    # Click the first result
    await target.click("result", custom_parameter=1)

    # Into detail page
    target.switch_page("DetailPage")
    rating: str = await target.get_value("rating")
    return rating


@pytest.mark.parametrize("target", [("target1", "target2")], indirect=True)
async def test_shawshank_rating(target):
    target1, target2 = target
    shawshank_rating = partial(
        query_rating, movie_or_book_name="The Shawshank Redemption"
    )

    movie_rating, book_rating = await asyncio.gather(
        shawshank_rating(target1), shawshank_rating(target2)
    )

    assert movie_rating == book_rating
