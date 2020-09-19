import asyncio
import inspect
from typing import Any, List

import pytest
from _pytest.nodes import Item


@pytest.mark.tryfirst
def pytest_collection_modifyitems(items: List["Item"]) -> None:
    """Called after collection of all test items is completed.

    Implement it to modify the items as follows:

    * Add `pytest.mark.asyncio`_ marker to each item.

    :param List[pytest.Item] items: The list of items objects.
    :return: None

    ..  _pytest.mark.asyncio:
        https://github.com/pytest-dev/pytest-asyncio#pytestmarkasyncio
    """
    items[:] = [add_asyncio_marker(item) for item in items]


def add_asyncio_marker(item: "Item") -> "pytest.Item":
    """Add `pytest.mark.asyncio`_ marker to the specified item.

    If the marker is already exists, return the item directly.

    :param pytest.Item item: The pytest item object.
    :return: The marked item object.

    ..  _pytest.mark.asyncio:
        https://github.com/pytest-dev/pytest-asyncio#pytestmarkasyncio
    """
    if "asyncio" not in item.keywords and is_coroutine(item.obj):
        item.add_marker(pytest.mark.asyncio)
    return item


def is_coroutine(obj: Any) -> bool:
    """Check to see if an object is really an asyncio coroutine.

    :param Any obj: Any object.
    :return: `True` or `False`.
    """
    return asyncio.iscoroutinefunction(obj) or inspect.isgeneratorfunction(obj)
