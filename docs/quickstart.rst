Quickstart
===========

For example, query the rating of the movie **The Shawshank Redemption** on `douban.com <https://movie.douban.com>`_.

.. code-block:: python

    from dataclasses import dataclass


    @dataclass(init=False)
    class Elements:
        url = "https://movie.douban.com/"

        query = "#inp-query"
        apply = ".inp-btn > input:nth-child(1)"

        result = (
            "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"
        )
        rating = (
            "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"
        )


    async def test_pyppteer(pyppeteer):
        page = await pyppeteer.new_page()
        await page.goto(Elements.url)

        await page.type(Elements.query, "The Shawshank Redemption")
        await page.click(Elements.apply)

        await page.waitfor(Elements.result)
        await page.click(Elements.result)

        await page.waitfor(Elements.rating)
        rating = await page.get_value(Elements.rating)
        assert rating == 0

The test will be failed because of ``assert rating == 0``, but we successfully got the rating of the movie, it was ``9.7``.

.. code-block:: bash

    $ pipenv run pytest -q tests/test_quickstart.py
    F                                                                              [100%]
    ====================================== FAILURES ======================================
    _________________________________ test_options_mark __________________________________

    pyppeteer = Browser(pyppeteer_browser=<pyppeteer.browser.Browser object at 0x10917e5e0>)

        async def test_options_mark(pyppeteer):
            page = await pyppeteer.new_page()
            await page.goto("https://movie.douban.com")

            await page.type(Elements.query, "The Shawshank Redemption")
            await page.click(Elements.apply)

            await page.waitfor(Elements.result)
            await page.click(Elements.result)

            await page.waitfor(Elements.rating)
            rating = await page.get_value(Elements.rating)
    >       assert rating == 0
    E       AssertionError: assert '9.7' == 0

    tests/test_quickstart.py:31: AssertionError
    ================================== warnings summary ==================================
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
    tests/test_quickstart.py::test_options_mark
      /Users/yaomeng/.local/share/virtualenvs/pytest-pyppeteer-KPzLwmKN/lib/python3.8/site-packages/pyee/_compat.py:35: DeprecationWarning: pyee.EventEmitter is deprecated and will be removed in a future major version; you should instead use either pyee.AsyncIOEventEmitter, pyee.TwistedEventEmitter, pyee.ExecutorEventEmitter, pyee.TrioEventEmitter, or pyee.BaseEventEmitter.
        warn(DeprecationWarning(

    -- Docs: https://docs.pytest.org/en/stable/warnings.html
    ============================== short test summary info ===============================
    FAILED tests/test_quickstart.py::test_options_mark - AssertionError: assert '9.7' == 0
    1 failed, 7 warnings in 7.61s

.. image:: image/quickstart.gif
   :alt: quickstart
   :align: left
