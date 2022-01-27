# flake8: noqa
from __future__ import annotations

import sys
from functools import reduce
from inspect import getmembers, getmodule, isfunction
from logging import getLogger
from types import MethodType
from typing import TYPE_CHECKING

import pytest
from _pytest.mark import Mark
from pyppeteer.launcher import launch

from pytest_pyppeteer import page

if TYPE_CHECKING:
    from typing import Callable, List, Optional

    from _pytest.config import Config as PytestConfig
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest
    from pyppeteer.browser import Browser
    from pyppeteer.page import Page

_page_functions = getmembers(
    page, lambda value: isfunction(value) and getmodule(value) is page and not value.__name__.startswith("_")
)

_chrome_executable_path = {
    "macos": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "win64": "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "win32": "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
}

logger = getLogger("pytest_pyppeteer")


async def new_page(self: Browser) -> Page:
    pyppeteer_page = await self.newPage()
    dimensions = await pyppeteer_page.evaluate(
        """() => {
            return {
                width: window.outerWidth,
                height: window.outerHeight,
                deviceScaleFactor: window.devicePixelRatio,
            }
        }"""
    )
    logger.debug("Resize the page viewport to {!r}.".format(dimensions))
    await pyppeteer_page.setViewport(dimensions)

    for name, func in _page_functions:
        logger.debug("Bind method {!r} to object {!r}.".format(name, pyppeteer_page))
        setattr(pyppeteer_page, name, MethodType(func, pyppeteer_page))
    return pyppeteer_page


def pytest_configure(config: PytestConfig) -> None:
    config.addinivalue_line("markers", "options(kwargs): update browser initial options.")


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("pyppeteer")
    group.addoption("--executable-path", default=None, help="Path to a Chromium or Chrome executable.")
    group.addoption("--headless", action="store_true", help="Run browser in headless mode.")
    group.addoption("--args", action="append", nargs="+", default=list(), help="Additional args passed to the browser.")
    group.addoption("--window-size", nargs=2, default=["800", "600"], help="Set the initial browser window size.")
    group.addoption("--slow", type=float, default=0.0, help="Slow down the operate in milliseconds.")


@pytest.fixture(scope="session")
def platform() -> Optional[str]:
    """Current platform. e.g. macos, win32, win64."""
    if sys.platform.startswith("darwin"):
        return "macos"
    elif sys.platform.startswith("win"):
        return "win64" if sys.maxsize > 2 ** 32 else "win32"
    else:
        logger.error(
            "Platform {!r} is unsupported. Currently only support {!r}.".format(
                sys.platform, tuple(_chrome_executable_path.keys())
            )
        )
        return None


@pytest.fixture(scope="session")
def default_executable_path(platform: Optional[str]) -> Optional[str]:
    """The default install path for Chrome browser in the current platform."""
    return _chrome_executable_path.pop(platform, None)


@pytest.fixture(scope="session")
def executable_path(pytestconfig: PytestConfig, default_executable_path: Optional[str]) -> Optional[str]:
    """The Chrome executable path for this test run."""
    return pytestconfig.getoption("executable_path") or default_executable_path


@pytest.fixture(scope="session")
def args(pytestconfig: PytestConfig) -> List[str]:
    """The extra args used to initialize Chrome browser."""
    return ["--" + "=".join(arg) for arg in pytestconfig.getoption("args")]


@pytest.fixture(scope="session")
def session_options(
    pytestconfig: PytestConfig, platform: Optional[str], executable_path: Optional[str], args: List[str]
) -> dict:
    """The default options used to initialize Chrome browser."""
    headless: bool = pytestconfig.getoption("headless")
    width, height = pytestconfig.getoption("window_size")
    slow: float = pytestconfig.getoption("slow")

    if width == height == "0":
        args.append("--start-fullscreen" if platform == "macos" else "--start-maximized")
    else:
        args.append("--window-size={},{}".format(width, height))

    return dict(headless=headless, slowMo=slow, args=args, executable_path=executable_path)


@pytest.fixture
def options(request: FixtureRequest, session_options: dict) -> dict:
    """The final options used to initialize Chrome browser."""
    options_mark: Mark = reduce(
        lambda mark1, mark2: mark1.combined_with(mark2),
        request.node.iter_markers("options"),
        Mark("options", args=tuple(), kwargs=dict()),
    )
    return dict(session_options, **options_mark.kwargs)


@pytest.fixture
async def browser_factory(options: dict) -> Callable[..., Browser]:
    """Provide to create a new browser instance."""
    browsers: List[Browser] = list()

    async def _factory() -> Browser:
        logger.debug("The options used to initialize the browser: {!r}".format(options))
        browser = await launch(**options)
        # logger.debug("Bind new method {!r} to browser instance {!r}.".format(new_page, browser))
        browser.new_page = MethodType(new_page, browser)
        browsers.append(browser)
        return browser

    yield _factory

    for browser in browsers:
        await browser.close()


@pytest.fixture
async def browser(browser_factory: Callable[..., Browser]) -> Browser:
    """Provide a new browser instance."""
    yield await browser_factory()
