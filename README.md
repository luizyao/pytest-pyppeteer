# pytest-pyppeteer
Test with [pyppeteer](https://github.com/pyppeteer/pyppeteer) in pytest.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-pyppeteer)
[![GitHub issues](https://img.shields.io/github/issues-raw/luizyao/pytest-pyppeteer)](https://github.com/luizyao/pytest-pyppeteer/issues)
[![PyPI](https://img.shields.io/pypi/v/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![gitmoji-changelog](https://img.shields.io/badge/Changelog-gitmoji-brightgreen.svg)](https://github.com/frinyvonnick/gitmoji-changelog)
[![GitHub](https://img.shields.io/github/license/luizyao/pytest-pyppeteer)](LICENSE)

# Installation

## Requirements
pytest-pyppeteer work with Python >=3.6.

## Install pytest-pyppeteer

```bash
pip install pytest-pyppeteer
```

or install latest one:

```bash
pip install git+https://github.com/luizyao/pytest-pyppeteer.git
```

# Quickstart
For example, compare the scores of a book and its movie on [Douban](https://www.douban.com).

## `--nptp, --new-pyppeteer-test-project`
Create a new pyppeteer test project in the specified path.

```bash
pytest --nptp=douban
```

The directory structure:

```bash
├── desc
├── pyproject.toml
└── test_douban.py

1 directory, 2 files
```

## Configuration

### `desc`
Create two files `douban_movie.desc` and `douban_book.desc` in `desc` directory.

> `[HomePage]` is required.

```toml
# douban_movie.desc

[HomePage]
#CSS
search_input = '#inp-query'
search_apply = '.inp-btn > input:nth-child(1)'

[SearchResultsPage]
# {} indicates that this part can be replaced by the custom parameter
# CSS
result = '#root > div > div > div > div > div:nth-child({}) > div.item-root a.cover-link'

[DetailPage]
rating = '#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong'
```

```toml
# douban_book.desc

[HomePage]
#CSS
search_input = '#inp-query'
search_apply = '.inp-btn > input:nth-child(1)'

[SearchResultsPage]
# {} indicates that this part can be replaced by the custom parameter
# Xpath
result = '(//*[@class="item-root"])[{}]/a'

[DetailPage]
rating = '#interest_sectl > div > div.rating_self.clearfix > strong'
```

### `pyproject.toml`
Add `target`:

```toml
[tool.pytest.pyppeteer.targets]
[tool.pytest.pyppeteer.targets.target1]
name = "douban_movie"
base_url = "https://movie.douban.com/"

[tool.pytest.pyppeteer.targets.target2]
name = "douban_book"
base_url = "https://book.douban.com/"
```

Path `executablePath` to a Chromium or Chrome executable.

```toml
[tool.pytest.pyppeteer.options]
executablePath = "/Applications/Chrome.app/Contents/MacOS/Google Chrome"
```

## Write tests
```python
# test_douban.py

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
    target1, target2 = target
    shawshank_rating = partial(query_rating, movie_or_book_name="肖申克的救赎")

    movie_rating, book_rating = await asyncio.gather(
        shawshank_rating(target1), shawshank_rating(target2)
    )

    assert movie_rating == book_rating
```

## Execute tests screenshot
![](assets/douban_example.gif)

# License
[MIT License](LICENSE)

# Changelog

<a name="0.1.1"></a>
## 0.1.1 (2020-08-22)

### Added

- ✨ add target.hover function [[c0fe87e](https://github.com/luizyao/pytest-pyppeteer/commit/c0fe87ee73d903072cb8d4c79592fdd3633bd3c8)]
 
### Fixed

- 🐛 fix issue [#4](https://github.com/luizyao/pytest-pyppeteer/issues/4) [[f2af677](https://github.com/luizyao/pytest-pyppeteer/commit/f2af6776ed02f56fb0fed1798d61d0c46a9202e2)]
- 🐛 fix issue [#2](https://github.com/luizyao/pytest-pyppeteer/issues/2) [[4537d16](https://github.com/luizyao/pytest-pyppeteer/commit/4537d16f95c2a5300b5fbbff12fe5eb42a880dab)]

> More details refer to [CHANGELOG](CHANGELOG.md).
