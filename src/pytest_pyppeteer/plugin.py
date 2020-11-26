import asyncio
import inspect
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, List, Optional

import pytest
from pyppeteer import launch

from pytest_pyppeteer.models import Browser, Options
from pytest_pyppeteer.utils import CHROME_EXECUTABLE, current_platform

if TYPE_CHECKING:
    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item
    from _pytest.runner import TestReport

LOGGER = logging.getLogger(__name__)


def pytest_addhooks(pluginmanager: "PytestPluginManager") -> None:
    """Add new hooks.

    :param _pytest.config.PytestPluginManager pluginmanager:
    :return: ``None``
    """
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_configure(config: "Config") -> None:
    """Perform initial configuration as follows:

    * Add ``pytest.mark.option`` marker to the ini-file option.

    :param _pyest.config.Config config: pytest config object.
    :return: None

    .. note::

        This is a ``pytest hook function`` which is called for
        every plugin and initial conftest file after command
        line options have been parsed. After that, the hook
        is called for other conftest files as they are imported.
    """
    config.addinivalue_line(
        "markers",
        "options(kwargs): add or change existing options. "
        "specify options as keyword argument, e.g. "
        "@pytest.mark.options(devtools=True)",
    )


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

        This is a ``pytest hook function`` which is called
        after collection of all test items is completed.

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


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: "Item") -> None:
    """Implement this pytest hook in wrapper mode, the added
    behaviors as follows:

    * Register a new
      :py:func:`hooks.pytest_pyppeteer_runtest_makereport_call_debug`
      hook which called when a actual failing test calls not setup/teardown.

    :param pytest.Item item: the pytest item object.
    :return: None
    """
    # execute all other hooks to obtain the report object
    outcome = yield
    res: TestReport = outcome.get_result()
    setattr(item, f"res_{res.when}", res)

    # we only deal with actual failing test calls, not setup/teardown
    if res.when == "call" and res.failed:
        hook: List[
            Awaitable
        ] = item.ihook.pytest_pyppeteer_runtest_makereport_call_debug(item=item)
        if hook:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(hook[0])


def pytest_addoption(parser: "Parser") -> None:
    """Register new command line arguments and ini-file values.

    Create a new command line option group named `pyppeteer`, and add the
    following new options in it:

    * ``--executable-path``: path to a Chromium or Chrome executable.

    * ``--headless``: run browser in headless mode.

    * ``--args``: additional args to pass to the browser instance. more
      details refer to :py:func:`args` fixture.

    * ``--window-size``: set the initial browser window size. Defaults
      to 800 * 600. ``--window-size 0 0`` means to starts the browser
      maximized.

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

    group.addoption(
        "--args",
        action="append",
        nargs="+",
        help="additional args to pass to the browser instance.",
    )

    group.addoption(
        "--window-size",
        nargs=2,
        default=["800", "600"],
        help="set the initial browser window size.",
    )

    group.addoption(
        "--slow", type=float, default=0.0, help="slow down the operate in milliseconds."
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
def args(pytestconfig: "Config") -> List[str]:
    """``Session-scoped fixture`` that return a list of additional
    args in the `List of Chromium Command Line Arguments`_ to pass
    to the browser instance.

    You can use it by command-line option:

    Example::

        $ pytest --args proxy-server "localhost:5555,direct://" --args proxy-bypass-list "192.0.0.1/8;10.0.0.1/8"

    Or overwrite it in your test:

    Example::

        @pytest.fixture(scope="session")
        def args(args) -> List[str]:
            return args + [
                "--proxy-server=localhost:5555,direct://",
                "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
            ]

    :param _pytest.config.Config pytestconfig: a session-scoped
           fixture that return config object.
    :return: a list of arguments string. return ``list()`` if no
             ``--args`` passed in the command-line.

    .. _List of Chromium Command Line Arguments:
       https://peter.sh/experiments/chromium-command-line-switches/
    """
    args: list = pytestconfig.getoption("--args")
    if args:
        return ["--" + "=".join(arg_list) for arg_list in args]
    else:
        return list()


@pytest.fixture(scope="session")
def session_options(
    pytestconfig: "Config", args: List[str], executable_path: str
) -> "Options":
    """``Session-scoped fixture`` that return a
    :py:class:`models.Options` object used to initialize browser.

    :param _pytest.config.Config pytestconfig: a session-scoped
           fixture that return config object.
    :param List[str] args: a session-scoped fixture that return
           a list of additional args to pass to the browser instance.
    :param str executable_path: a session-scoped fixture that return
           Chrome or Chromium executable path.
    :return: a :py:class:`models.Options` object used to initialize
             browser.
    """
    headless: bool = pytestconfig.getoption("--headless")
    width, hight = pytestconfig.getoption("--window-size")
    slow: float = pytestconfig.getoption("--slow")
    if width == "0" and hight == "0":
        if current_platform() == "mac":
            args.append("--start-fullscreen")
        else:
            args.append("--start-maximized")
    else:
        args.append("--window-size={},{}".format(width, hight))
    return Options(
        args=args, executablePath=executable_path, headless=headless, slowMo=slow
    )


@pytest.fixture
def options(request: "FixtureRequest", session_options: "Options") -> "Options":
    """``Function-scoped fixture`` that return a
    :py:class:`models.Options` object used to initialize browser.

    This fixture contains all of :py:func:`session_options`, plus
    any options specified by the options markers. Any change to
    these options will apply only to the tests covered by scope
    of the fixture override.

    Example::

        @pytest.mark.options(devtools=True)
        async def test_options_mark(pyppeteer):
            ...

    :param _pytest.fixture.FixtureRequest request: A request
           object gives access to the requesting test context.
    :param Options session_options: a :py:class:`models.Options`
           object from :py:func:`session_options`.
    :return: a :py:class:`models.Options` object used to initialize
             browser.
    """
    return session_options.copy(update=get_options_from_markers(request.node))


def get_options_from_markers(item: "Item") -> dict:
    """Get the options from the ``options`` markers of test item.
    And there are only apply on the current test item.

    :param Item item: the test item object.
    :return: an dict contains options.
    """
    options_dict = dict()
    for node, mark in item.iter_markers_with_node("options"):
        LOGGER.debug(
            "{0} marker <{1.name}> "
            "contains kwargs <{1.kwargs}>".format(node.__class__.__name__, mark)
        )
        options_dict.update(mark.kwargs)
    LOGGER.info("Options from markers: {}".format(options_dict))
    return options_dict


@pytest.fixture
async def pyppeteer_factory(options: "Options") -> Callable:
    """``Function-scoped fixture`` that return a pyppeteer
    browser factory.

    :param Options options: a :py:class:`models.Options`
           object used to initialize browser
    :yield: a pyppeteer browser factory.
    """
    browsers: List[Browser] = list()

    async def _factory() -> "Browser":
        LOGGER.info("Options to initialize browser instance: {}".format(options))
        b = Browser(pyppeteer_browser=await launch(options=options.dict()))
        browsers.append(b)
        return b

    yield _factory

    for browser in browsers:
        await browser.close()


@pytest.fixture
async def pyppeteer(pyppeteer_factory: "Callable") -> "Browser":
    """``Function-scoped fixture`` that return a pyppeteer
    browser instance.

    :param Callable pyppeteer_factory: pyppeteer factory
    :yield: a pyppeteer browser instance.
    """
    yield await pyppeteer_factory()
