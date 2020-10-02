Advanced Usage
==============

Control multiple browsers asynchronously
----------------------------------------

You can easily to control multiple browsers at the same time.

For example, query the **The Shawshank Redemption**'s movie
and book rating on `douban.com <https://movie.douban.com>`_
at the same time, then compare them.

.. code-block:: python

    import asyncio
    from dataclasses import dataclass
    from typing import TYPE_CHECKING, Callable

    import pytest

    if TYPE_CHECKING:
        from .models import Browser, Page


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


    async def test_multiple_browsers(pyppeteer_factory: "Callable"):
        pyppeteer1 = await pyppeteer_factory()
        pyppeteer2 = await pyppeteer_factory()

        movie_rating, book_rating = await asyncio.gather(
            query_rating(pyppeteer1, "The Shawshank Redemption", MovieElements),
            query_rating(pyppeteer2, "The Shawshank Redemption", BookElements),
        )

        assert movie_rating == book_rating

Execute this test, and it will be failed:

.. code-block:: bash

    $ pipenv run pytest -q tests/test_multiple_browsers.py
    F                                                                              [100%]
    ====================================== FAILURES ======================================
    _______________________________ test_multiple_browsers _______________________________

    pyppeteer_factory = <function pyppeteer_factory.<locals>._factory at 0x1068c4700>

        async def test_multiple_browsers(pyppeteer_factory: "Callable"):
            pyppeteer1 = await pyppeteer_factory()
            pyppeteer2 = await pyppeteer_factory()

            movie_rating, book_rating = await asyncio.gather(
                query_rating(pyppeteer1, "The Shawshank Redemption", MovieElements),
                query_rating(pyppeteer2, "The Shawshank Redemption", BookElements),
            )

    >       assert movie_rating == book_rating
    E       AssertionError: assert '9.7' == '9.2'
    E         - 9.2
    E         + 9.7

    tests/test_multiple_browsers.py:62: AssertionError
    ================================== warnings summary ==================================
    tests/test_multiple_browsers.py: 14 warnings
      /Users/yaomeng/.local/share/virtualenvs/pytest-pyppeteer-KPzLwmKN/lib/python3.8/site-packages/pyee/_compat.py:35: DeprecationWarning: pyee.EventEmitter is deprecated and will be removed in a future major version; you should instead use either pyee.AsyncIOEventEmitter, pyee.TwistedEventEmitter, pyee.ExecutorEventEmitter, pyee.TrioEventEmitter, or pyee.BaseEventEmitter.
        warn(DeprecationWarning(

    -- Docs: https://docs.pytest.org/en/stable/warnings.html
    ============================== short test summary info ===============================
    FAILED tests/test_multiple_browsers.py::test_multiple_browsers - AssertionError: as...
    1 failed, 14 warnings in 17.58s


.. image:: image/multiple_browsers.gif
   :alt: multiple_browsers
   :align: left
