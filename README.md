## pytest-pyppeteer
Test with [pyppeteer](https://github.com/pyppeteer/pyppeteer) in pytest.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-pyppeteer)](https://pypi.org/project/pytest-pyppeteer/)
![GitHub issues](https://img.shields.io/github/issues-raw/luizyao/pytest-pyppeteer)
![PyPI](https://img.shields.io/pypi/v/pytest-pyppeteer)
![GitHub](https://img.shields.io/github/license/luizyao/pytest-pyppeteer)

## Installation

### Requirements
pytest-pyppeteer work with Python >=3.6.

### Install pytest-pyppeteer

```bash
pip install pytest-pyppeteer
```

## Usage
For example, compare the scores of a book and its movie on [Douban](https://www.douban.com).

### `--nptp, --new-pyppeteer-test-project`
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

### Configuration

#### `desc`
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
result = '#root > div > div > div > div > div:nth-child({}) > div.item-root a.cover-link'

[DetailPage]
rating = '#interest_sectl > div > div.rating_self.clearfix > strong'
```

#### `pyproject.toml`
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

### Write tests
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

### Execute tests
![](assets/douban_example.gif)

## License
[MIT License](LICENSE)
