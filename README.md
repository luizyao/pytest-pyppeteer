# pytest-pyppeteer
A plugin to run [pyppeteer](https://github.com/pyppeteer/pyppeteer) in pytest.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-pyppeteer)
[![GitHub issues](https://img.shields.io/github/issues-raw/luizyao/pytest-pyppeteer)](https://github.com/luizyao/pytest-pyppeteer/issues)
[![PyPI](https://img.shields.io/pypi/v/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/pytest-pyppeteer/badge/?version=latest)](https://pytest-pyppeteer.readthedocs.io/en/latest/?badge=latest)

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

For example, query the rating of the movie **The Shawshank Redemption** on [douban.com](https://movie.douban.com).

```python
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


async def test_pyppeteer(pyppeteer):
    page = await pyppeteer.new_page()
    await page.goto(Elements.url)

    await page.type(Elements.query, "The Shawshank Redemption")
    await page.click(Elements.apply)

    await page.waitfor(Elements.result)
    await page.click(Elements.result)

    await page.waitfor(Elements.rating)
    rating = await page.get_value(Elements.rating)
    assert rating == 0
```


# License
Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT) license, pytest-pyppeteer is free and open source software.


# Issues
If you encounter any problems, please [file an issue](https://github.com/luizyao/pytest-pyppeteer/issues) along with a detailed description.
