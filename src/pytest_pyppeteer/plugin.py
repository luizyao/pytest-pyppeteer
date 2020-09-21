import asyncio
import inspect
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import pytest
from pyppeteer import launch

from pytest_pyppeteer.models import Options
from pytest_pyppeteer.utils import CHROME_EXECUTABLE, current_platform

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
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

    * ``--headless``: run browser in headless mode.

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
        "--executable-path", help="path to a Chromium or Chrome executable."
    )

    group.addoption(
        "--headless", action="store_true", help="run browser in headless mode."
    )


@pytest.fixture(scope="session")
def executable_path(pytestconfig: "Config") -> Optional[str]:
    """``Session-scoped fixture`` that return Chrome or Chromium executable path.

    The fixture behaviors follow this procedure:

    1. Return the value passed in from command line option of `--executable-path`,
       if it's not ``None``.

    2. Return the default installation location of Chrome in current platform,
       but now only support ``win64``, ``win32`` and ``mac`` platform.

       For other platforms, pyppeteer will downloads the recent version of Chromium
       when called first time. If you don't prefer this behavior, you can specify
       an exact path by overwrite this fixture:

       Example::

           @pytest.fixture(scope="session")
           def executable_path(executable_path):
               if executable_path is None:
                   return "path/to/Chrome/or/Chromium"
               return executable_path


    :param _pytest.config.Config pytestconfig: a session-scoped fixture that return
           config object.
    :return: return Chrome or Chromium executable path string. but if current platform
             isn't supported, return ``None``.
    """
    path = pytestconfig.getoption("--executable-path")
    if path:
        return path

    try:
        return CHROME_EXECUTABLE[current_platform()]
    except OSError as e:
        # Unsupported platform
        LOGGER.error(e)
        return None


@pytest.fixture(scope="session")
def session_options(pytestconfig: "Config", executable_path: str) -> Options:
    headless: bool = pytestconfig.getoption("--headless")
    return Options(executablePath=executable_path, headless=headless)


@pytest.fixture
async def pyppeteer(session_options: Options):
    browser = await launch(options=session_options.dict())
    yield browser
    await browser.close()
