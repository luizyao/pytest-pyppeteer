import asyncio
from functools import partial

import pytest
from pytest_pyppeteer.models import Pyppeteer


async def query_rating(target: Pyppeteer, movie_or_book_name: str):
    await target.open(goto_base_url=True)
    await target.input("search_input", text=movie_or_book_name)
    await target.click("search_apply")

    # Into search results page
    target.switch_page("SearchResultsPage")
    # Click the first result
    await target.click("result", custom_parameter=(1,))

    # Into detail page
    target.switch_page("DetailPage")
    rating: str = await target.get_value("rating")
    await target.close()
    return rating


@pytest.mark.parametrize("target", [("target1", "target2")], indirect=True)
async def test_shawshank_rating(target):
    shawshank_rating = partial(query_rating, movie_or_book_name="肖申克的救赎")

    movie_rating, book_rating = await asyncio.gather(*map(shawshank_rating, target))

    assert movie_rating == book_rating
