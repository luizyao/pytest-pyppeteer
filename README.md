# pytest-pyppeteer

A plugin to run [pyppeteer](https://github.com/pyppeteer/pyppeteer) in pytest.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-pyppeteer)
[![GitHub issues](https://img.shields.io/github/issues-raw/luizyao/pytest-pyppeteer)](https://github.com/luizyao/pytest-pyppeteer/issues)
[![PyPI](https://img.shields.io/pypi/v/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![Downloads](https://pepy.tech/badge/pytest-pyppeteer)](https://pepy.tech/project/pytest-pyppeteer)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Installation

You can install pytest-pyppeteer via [pip](https://pypi.org/project/pip/):

```bash
$ pip install pytest-pyppeteer
```

or install the latest one on Github:

```bash
pip install git+https://github.com/luizyao/pytest-pyppeteer.git
```

# Quickstart

For example, **The Shawshank Redemption** deserves a 9.0 or higher rating on [douban.com](https://movie.douban.com).

```python
from dataclasses import dataclass


@dataclass(init=False)
class Elements:
    """Collect locators of page objects, no matter XPath or CSS Selector."""

    # query input
    query = "#inp-query"

    # search button
    apply = ".inp-btn > input:nth-child(1)"

    # the first result
    first_result = "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"

    # rating
    rating = "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"


async def test_lifetimes(browser):
    page = await browser.new_page()
    await page.goto("https://movie.douban.com/")

    await page.type(Elements.query, "The Shawshank Redemption")
    await page.click(Elements.apply)

    await page.waitfor(Elements.first_result)
    await page.click(Elements.first_result)

    await page.waitfor(Elements.rating)
    rating = await page.get_value(Elements.rating)

    assert float(rating) >= 9.0
```

![quickstart](images/quickstart.gif)

# Usage

## Fixtures

### `browser` fixture

Provide an `pyppeteer.browser.Browser` instance with a new method `new_page()`, like `pyppeteer.browser.Browser.newPage()`, `new_page()` could create a `pyppeteer.page.Page` instance.

But the `pyppeteer.page.Page` instance created by `new_page()` has some new methods:

| Method        | Type     |
| ------------- | -------- |
| query_locator | New      |
| waitfor       | New      |
| click         | Override |
| type          | Override |
| get_value     | New      |

For example, you can query an element by css or xpath in the same method `query_locator` instead of original `querySelector` and `xpath`.

> More details check with [page.py](src/pytest_pyppeteer/page.py) in the source code.

### `browser_factory` fixture

Provide to create an `pyppeteer.browser.Browser` instance.

For example, query the **The Shawshank Redemption**’s movie and book rating on [douban.com](https://movie.douban.com/) at the same time, then compare them.

```python
import asyncio
from dataclasses import dataclass


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

    result = "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"
    rating = "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"


async def query_rating(browser, name: str, elements: "Elements"):
    page = await browser.new_page()

    await page.goto(elements.url)

    await page.type(elements.query, name)
    await page.click(elements.apply)

    await page.waitfor(elements.result)
    await page.click(elements.result)

    await page.waitfor(elements.rating)
    rating = await page.get_value(elements.rating)
    return rating


async def test_multiple_browsers(browser_factory):
    browser1 = await browser_factory()
    browser2 = await browser_factory()

    movie_rating, book_rating = await asyncio.gather(
        query_rating(browser1, "The Shawshank Redemption", MovieElements),
        query_rating(browser2, "The Shawshank Redemption", BookElements),
    )

    assert movie_rating == book_rating
```

![multiple_browsers](images/multiple_browsers.gif)

## Command line options

### `--executable-path`

You can specify the Chromium or Chrome executable path. Otherwise I will use the default install path of Chrome in current platform.

For other platforms, pyppeteer will downloads the recent version of Chromium when called first time. If you don’t prefer this behavior, you can specify an exact path by override this fixture:

```python
@pytest.fixture(scope="session")
def executable_path(executable_path):
    return executable_path or "path/to/Chrome/or/Chromium"
```

### `--headless`

Run browser in headless mode.

### `--args`

Additional args to pass to the browser instance.

For example, specify a proxy:

```bash
$ pytest --args proxy-server "localhost:5555,direct://" --args proxy-bypass-list "192.0.0.1/8;10.0.0.1/8"
```

Or by override the `args` fixture:

```python
@pytest.fixture(scope="session")
def args(args) -> List[str]:
    return args + [
        "--proxy-server=localhost:5555,direct://",
        "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
    ]
```

### `--window-size`

The default browser size is 800\*600, you can use this option to change this behavior:

```bash
$ pytest --window-size 1200 800
```

`--window-size 0 0` means to starts the browser maximized.

### `--slow`

Slow down the pyppeteer operate in milliseconds. Defaults to `0.0`.

## Markers

### `options`

You can override some command line options in the specified test.

For example, auto-open a DevTools panel:

```python
import asyncio

import pytest


@pytest.mark.options(devtools=True)
async def test_marker(browser):
    await browser.new_page()
    await asyncio.sleep(2)
```

![options marker](images/options_marker.gif)

# License

Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT) license, pytest-pyppeteer is free and open source software.

# Issues

If you encounter any problems, please [file an issue](https://github.com/luizyao/pytest-pyppeteer/issues) along with a detailed description.
