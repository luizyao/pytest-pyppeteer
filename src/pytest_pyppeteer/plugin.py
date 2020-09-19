import asyncio
import inspect
import os
from argparse import ArgumentTypeError
from typing import Any, List

import pytest

from pytest_pyppeteer import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item


@pytest.mark.tryfirst
def pytest_collection_modifyitems(items: List["Item"]) -> None:
    """Modify the items collected by pytest as follows:

    * Because all test items using pyppeteer should be an
      asyncio coroutine, here the `pytest.mark.asyncio`_
      marker is automatically added to each test item
      collected by pytest.

    :param List[pytest.Item] items: the list of items objects
           collected by pytest.
    :return: None

    .. note::

        This is a ``pytest hook function`` which be called after collection
        of all test items is completed.

    ..  _pytest.mark.asyncio:
        https://github.com/pytest-dev/pytest-asyncio#pytestmarkasyncio
    """
    items[:] = [add_asyncio_marker(item) for item in items]


def add_asyncio_marker(item: "Item") -> "Item":
    """Add `pytest.mark.asyncio`_ marker to the specified item.

    If the marker is already exists, return the item directly.

    :param pytest.Item item: the pytest item object.
    :return: the marked item object.

    ..  _pytest.mark.asyncio:
        https://github.com/pytest-dev/pytest-asyncio#pytestmarkasyncio
    """
    if "asyncio" not in item.keywords and is_coroutine(item.obj):
        item.add_marker(pytest.mark.asyncio)
    return item


def is_coroutine(obj: Any) -> bool:
    """Check to see if an object is really an asyncio coroutine.

    :param Any obj: any object.
    :return: `True` or `False`.
    """
    return asyncio.iscoroutinefunction(obj) or inspect.isgeneratorfunction(obj)


def pytest_addoption(parser: "Parser") -> None:
    """Register new command line arguments and ini-file values.

    Create a new command line option group named `pyppeteer`, and add the
    following new arguments in it:

    * ``--executable-path``: path to a Chromium or Chrome executable

    :param _pytest.config.argparsing.Parser parser: parser for command
           line arguments and ini-file values.
    :return: None

    .. note::

        This is a ``pytest hook function`` which be called once at the beginning
        of a test run to register argparse-style options and ini-style config values.

        There are two ways to register new options, respectively:

        * To register a command line option, call
          :py:meth:`parser.addoption(...) <pytest:_pytest.config.argparsing.Parser.addoption>`.

        * To register an ini-file option, call
          :py:meth:`parser.addini(...) <pytest:_pytest.config.argparsing.Parser.addini>`.

        And the options can later be accessed through the
        :py:class:`Config <pytest:_pytest.config.Config>` object, respectively:

        * To retrieve the value of a command line option, call
          :py:meth:`config.getoption(name) <pytest:_pytest.config.Config.getoption>`.

        * To retrieve a value read from an ini-style file, call
          :py:meth:`config.getini(name) <pytest:_pytest.config.Config.getini>`.

        The ``Config`` object is passed around on many pytest internal objects via the
        ``.config`` attribute or can be retrieved as the
        :py:func:`pytestconfig <pytest:_pytest.fixtures.pytestconfig>` fixture.
    """
    # Create a option group named "pyppeteer"
    group = parser.getgroup("pyppeteer", description="pyppeteer")
    group.addoption(
        "--executable-path",
        type=existed_executable,
        help="path to a Chromium or Chrome executable.",
    )


def existed_executable(path: str) -> str:
    """Filter the path string which does not point to a executable file.

    The behaviors used in this plugin:

    * Called once the ``--executable-path`` option passed in from the command line.

    :param str path: a path string.
    :return: a path string point to the executable.
    :raise ArgumentTypeError: if path does not point to a executable file.
    """
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        msg = 'path "{}" does not point to a executable file'.format(
            os.path.abspath(path)
        )
        raise ArgumentTypeError(msg)
    return path
