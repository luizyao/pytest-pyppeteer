# pytest-pyppeteer
A plugin to run [pyppeteer](https://github.com/pyppeteer/pyppeteer) in pytest.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-pyppeteer)
[![GitHub issues](https://img.shields.io/github/issues-raw/luizyao/pytest-pyppeteer)](https://github.com/luizyao/pytest-pyppeteer/issues)
[![PyPI](https://img.shields.io/pypi/v/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![Downloads](https://pepy.tech/badge/pytest-pyppeteer)](https://pepy.tech/project/pytest-pyppeteer)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/pytest-pyppeteer/badge/?version=latest)](https://pytest-pyppeteer.readthedocs.io/en/latest/?badge=latest)
[![中文博客](https://img.shields.io/badge/blog-%E4%B8%AD%E6%96%87%E5%8D%9A%E5%AE%A2-yellowgreen)](https://luizyao.com/blog/post/2020-11-06-run-pyppeteer-in-pytest/)

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

from pytest_pyppeteer.models import Browser


@dataclass(init=False)
class Elements:
    """Collect locators of page objects, no matter XPath or CSS Selector."""

    # query input
    query = "#inp-query"

    # search button
    apply = ".inp-btn > input:nth-child(1)"

    # the first result
    first_result = (
        "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"
    )

    # rating
    rating = (
        "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"
    )


async def test_lifetimes(pyppeteer: Browser):
    page = await pyppeteer.new_page()
    await page.goto('https://movie.douban.com/')

    await page.type(Elements.query, "The Shawshank Redemption")
    await page.click(Elements.apply)

    await page.waitfor(Elements.first_result)
    await page.click(Elements.first_result)

    await page.waitfor(Elements.rating)
    rating = await page.get_value(Elements.rating)
    
    assert float(rating) >= 9.0
```

![quickstart](https://pytest-pyppeteer.readthedocs.io/en/latest/_images/quickstart.gif)

# Usage

## Command line options

### `--executable-path`

You can specify the path to a Chromium or Chrome executable. otherwise pytest-pyppeteer will use the default installation location of Chrome in current platform, but now only support `win64`, `win32` and `mac` platform.

For other platforms, pyppeteer will downloads the recent version of Chromium when called first time. If you don’t prefer this behavior, you can specify an exact path by override this fixture:

```python
@pytest.fixture(scope="session")
def executable_path(executable_path):
    if executable_path is None:
        return "path/to/Chrome/or/Chromium"
    return executable_path
```

> **Note**:
>
> The default installation location of Chrome in different platform:
>
> - `win64`: C:/Program Files/Google/Chrome/Application/chrome.exe
> - `win32`: C:/Program Files (x86)/Google/Chrome/Application/chrome.exe
> - `mac`: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome

### `--headless`

Run browser in headless mode.

### `--args`

Additional args to pass to the browser instance.

For example, specify a proxy:

```
$ pytest --args proxy-server "localhost:5555,direct://" --args proxy-bypass-list "192.0.0.1/8;10.0.0.1/8"
```

Or by override the `args` fixture:

```
@pytest.fixture(scope="session")
def args(args) -> List[str]:
    return args + [
        "--proxy-server=localhost:5555,direct://",
        "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
    ]
```

### `--window-size`

The default browser size is 800*600, you can use this option to change this behavior:

```
$ pytest --window-size 1200 800
```

`--window-size 0 0` means to starts the browser maximized.

### `--slow`

Slow down the pyppeteer operate in milliseconds. Defaults to `0.0`.

## No matter selector or xpath

`pyppeteer` fixture provide a `pytest_pyppeteer.models.Browser` instance, its usage is almost the same as `pyppeteer.browser.Browser`, except that it provides a new instance method: `new_page()`, which is similar to `newPage()`, but it returns a `pytest_pyppeteer.models.Page` instead of `pyppeteer.page.Page`.

`pytest_pyppeteer.models.Page`’s usage is also the same as `pyppeteer.page.Page`, but it provides some new instance methods, and override some methods. For example, you can query an element by selector or xpath in just same method `query_locator` instead of original `querySelector` and `xpath`.

You can also get an original `Page` by `pyppeteer.newPage()`.

## `options` marker

You can override some command line options in the specified test.

For example, auto-open a DevTools panel:

```python
import asyncio

import pytest


@pytest.mark.options(devtools=True)
async def test_marker(pyppeteer):
    await pyppeteer.new_page()
    await asyncio.sleep(2)
```

![options marker](https://pytest-pyppeteer.readthedocs.io/en/latest/_images/options_marker.gif)

# Advanced Usage

## Control multiple browsers asynchronously

You can easily to control multiple browsers at the same time.

For example, query the **The Shawshank Redemption**’s movie and book rating on [douban.com](https://movie.douban.com/) at the same time, then compare them.

```python
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
```

![multiple_browsers](https://pytest-pyppeteer.readthedocs.io/en/latest/_images/multiple_browsers.gif)

# License

Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT) license, pytest-pyppeteer is free and open source software.


# Issues
If you encounter any problems, please [file an issue](https://github.com/luizyao/pytest-pyppeteer/issues) along with a detailed description.
