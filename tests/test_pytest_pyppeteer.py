import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Union

import pytest

if TYPE_CHECKING:
    from pytest_pyppeteer.models import Browser, Page


@dataclass
class Elements:
    query = "#inp-query"
    apply = ".inp-btn > input:nth-child(1)"


@dataclass
class BookElements(Elements):
    url = "https://book.douban.com/"

    result = '(//*[@class="item-root"])[1]/a'
    rating = "#interest_sectl > div > div.rating_self.clearfix > strong"


@dataclass
class MovieElements(Elements):
    url = "https://movie.douban.com/"

    result = (
        "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"
    )
    rating = (
        "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"
    )


async def query_rating(pyppeteer: "Browser", name: str, elements: "Elements"):
    page: Page = await pyppeteer.new_page()

    await page.goto(elements.url)

    await page.type(elements.query, name)
    await page.click(elements.apply)

    await page.waitfor(elements.result)
    await page.click(elements.result)

    await page.waitfor(elements.rating)
    rating = await page.get_value(elements.rating)
    return rating


# Starts the browser maximized
@pytest.mark.options(args=["--window-size 1200,800"], devtools=True)
async def test_options_mark(pyppeteer):
    page = await pyppeteer.new_page()
    await page.goto("https://douban.com")
    assert 0


async def test_pyppeteer(pyppeteer: "Browser"):
    await query_rating(pyppeteer, "One Flew Over the Cuckoo's Nest", MovieElements)


async def test_pyppeteer_factory(pyppeteer_factory: "Callable"):
    pyppeteer1 = await pyppeteer_factory()
    pyppeteer2 = await pyppeteer_factory()

    movie_rating, book_rating = await asyncio.gather(
        query_rating(pyppeteer1, "The Shawshank Redemption", MovieElements),
        query_rating(pyppeteer2, "The Shawshank Redemption", BookElements),
    )

    assert movie_rating == book_rating
