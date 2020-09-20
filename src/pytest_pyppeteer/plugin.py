import asyncio
import inspect
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import pytest

from pytest_pyppeteer.errors import PathNotAExecutableError
from pytest_pyppeteer.utils import (
    CHROME_EXECUTABLE,
    current_platform,
    existed_executable,
)

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item

LOGGER = logging.getLogger(__name__)


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
    following new options in it:

    * ``--executable-path``: path to a Chromium or Chrome executable.

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


@pytest.fixture(scope="session")
def executable_path(request: "FixtureRequest") -> Optional[str]:
    """``Session-scoped fixture`` that return Chrome or Chromium executable path.

    The fixture behaviors follow this procedure:

    1. Retrieve the value passed in from command line option of `--executable-path`.
       if the value is not ``None``, return it.

    2. If Chrome(not Chromium) is installed in default location, return it. Now only
       support ``win64``, ``win32`` and ``mac`` platform.
    
    3. Return ``None``. In this case, pyppeteer will downloads the recent
       version Chromium when called in the first time. If you don’t prefer this
       behavior, you can overwrite this fixture to specify another executable
       path string.

       Example::

           @pytest.fixture(scope="session")
           def executable_path(executable_path):
               if executable_path is None:
                   return "path/to/Chrome/or/Chromium"
               return executable_path

    :param _pytest.fixtures.FixtureRequest request: a fixture providing
           information of the requesting test function.
    :return: Chrome or Chromium executable path string.
    """
    path = request.config.getoption("--executable-path")
    if path:
        LOGGER.info(
            'User-specified Chrome or Chromium executable path "{}"'.format(path)
        )
        return path

    try:
        platform = current_platform()
    except OSError as e:
        # Unsupported platform
        LOGGER.error(e.args[0])
        return None
    else:
        LOGGER.info('Current platform is "{}"'.format(platform))

    default_path = CHROME_EXECUTABLE[platform]
    try:
        path = existed_executable(default_path)
    except PathNotAExecutableError:
        LOGGER.info(
            'Chrome is not installed or not installed in the default path "{}".'.format(
                default_path
            )
        )
        return None
    else:
        LOGGER.info('Find the Chrome executable in the path: "{}"'.format(path))
        return path
