import asyncio
import logging
import os
from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import BaseModel, validator
from pyppeteer.browser import Browser as PyppeteerBrowser
from pyppeteer.errors import ElementHandleError, TimeoutError
from pyppeteer.page import Page as PyppeteerPage

from pytest_pyppeteer.errors import (
    ElementNotExistError,
    ElementTimeoutError,
    PathNotAExecutableError,
)
from pytest_pyppeteer.utils import parse_locator

if TYPE_CHECKING:
    from pyppeteer.element_handle import ElementHandle
    from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ViewPort(BaseModel):
    """Keep the consistency of each page's viewport in a browser instance.

    One of the most important use is as the standard setting model for
    :py:class:`Options.defaultViewport`.
    """

    #: Page width in pixels. Defaults to ``800``.
    width: int = 800

    #: Page height in pixels. Defaults to ``600``.
    height: int = 600

    #: Specify device scale factor (can be thought of as dpr).
    #: Defaults to ``1.0``.
    deviceScaleFactor: float = 1.0

    #: Whether the ``meta viewport`` tag is taken into account.
    #: Defaults to ``False``.
    isMobile: bool = False

    #: Specifies if viewport supports touch events. Defaults to ``False``.
    hasTouch: bool = False

    #: Specifies if viewport is in landscape mode. Defaults to ``False``.
    isLandscape: bool = False


class Options(BaseModel):
    """The standard setting model for pyppeteer launcher."""

    #: Additional arguments to pass to the browser instance. The list
    #: of Chromium flags can be found
    #: `here <https://peter.sh/experiments/chromium-command-line-switches/>`_.
    #: Defaults to ``list()``.
    args: List[str] = list()

    #: Automatically close browser process when script completed.
    #: Defaults to ``True``.
    autoClose: bool = True

    #: Set a consistent viewport for each page. Defaults to a default
    #: :py:class:`ViewPort` instance. ``None`` means disables the
    #: default viewport.
    defaultViewport: Optional["ViewPort"] = ViewPort()

    #: Whether to auto-open a DevTools panel for each tab. If this
    #: option is ``True``, the ``headless`` option will be set ``False``.
    #: Defaults to ``False``.
    devtools: bool = False

    #: Whether to pipe the browser process stdout and stderr into
    #: ``process.stdout`` and ``process.stderr``. Defaults to ``False``.
    dumpio: bool = False

    #: Specify environment variables that will be visible to the
    #: browser. ``None`` means that same as python process.
    #: Defaults to ``None``.
    env: Optional[dict] = None

    #: Path to a Chromium or Chrome executable. ``None`` means use the
    #: default bundled Chromium. Defaults to ``None``.
    executablePath: Union[str, "Path"] = None

    #: Close the browser process on `Ctrl-C`. Defaults to ``True``.
    handleSIGINT: bool = True

    #: Close the browser process on `SIGTERM`. Defaults to ``True``.
    handleSIGTERM: bool = True

    #: Close the browser process on `SIGHUP`. Defaults to ``True``.
    handleSIGHUP: bool = True

    #: Whether to run browser in headless mode. Defaults to ``False``.
    headless: bool = False

    #: Whether to ignore HTTPS errors. Defaults to ``True``.
    ignoreHTTPSErrors: bool = True

    #: If ``True``, then do not use pyppeteer's default args. If a
    #: list is given, then filter out the given default args.
    #: Dangerous option; use with care. Defaults to ``False``.
    ignoreDefaultArgs: Union[bool, List[str]] = False

    #: Log level to print logs. ``None`` means that same as the root logger.
    #: Defaults to ``None``.
    logLevel: Union[int, str, None] = None

    #: Slow down operations by the specified amount of milliseconds.
    #: useful so that you can see what is going on. Defaults to ``0.0``.
    slowMo: float = 0.0

    #: Path to a
    #: `User Data Directory <https://chromium.googlesource.com/chromium/src/+/master/docs/user_data_dir.md>`_.
    #: Defaults to ``None``.
    userDataDir: Optional[str] = None

    class Config:
        """Control the behaviours of pydantic model."""

        #: whether to allow arbitrary user types for fields (they are
        #: validated simply by checking if the value is an instance
        #: of the type). If False, RuntimeError will be raised on model
        #: declaration.
        arbitrary_types_allowed = True

    @validator("executablePath", pre=True)
    def validate_executable_path(cls, path: Optional[str]) -> Optional[str]:
        """Validate that the specified ``executablePath`` must point
        to an executable.

        :param str path: path string.
        :return: path string.
        :raise PathNotAExecutableError: if path does not point to a
               executable file.
        """
        if path and not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise PathNotAExecutableError(path=os.path.abspath(path))
        return path


class Browser(BaseModel):
    #: a pyppeteer browser object.
    pyppeteer_browser: "PyppeteerBrowser"

    class Config:
        """Control the behaviours of pydantic model."""

        #: whether to allow arbitrary user types for fields (they are
        #: validated simply by checking if the value is an instance
        #: of the type). If False, RuntimeError will be raised on model
        #: declaration.
        arbitrary_types_allowed = True

    def __getattr__(self, name):
        return getattr(self.pyppeteer_browser, name)

    async def new_page(self) -> "Page":
        """Make new page on this browser and return its object.

        :return: a :py:class:`Page` object.
        """
        pyppeteer_page = await self.pyppeteer_browser.newPage()
        # Make sure page and browser size as same.
        dimensions = await pyppeteer_page.evaluate(
            """() => {
            return {
                width: window.outerWidth,
                height: window.outerHeight,
                deviceScaleFactor: window.devicePixelRatio,
            }
        }"""
        )
        LOGGER.info('Resize page viewport to "{}"'.format(dimensions))
        await pyppeteer_page.setViewport(dimensions)
        return Page(pyppeteer_page=pyppeteer_page)


async def _clickable(element: "ElementHandle") -> None:
    for i in range(10):
        try:
            await element._clickablePoint()
        except ElementHandleError as e:
            LOGGER.error(e)
            LOGGER.info("Element not clickable. waiting... and try again.")
            await asyncio.sleep(0.5)
        else:
            break


class Page(BaseModel):
    #: a pyppeteer page object.
    pyppeteer_page: "PyppeteerPage"

    class Config:
        """Control the behaviours of pydantic model."""

        #: whether to allow arbitrary user types for fields (they are
        #: validated simply by checking if the value is an instance
        #: of the type). If False, RuntimeError will be raised on model
        #: declaration.
        arbitrary_types_allowed = True

    def __getattr__(self, name):
        return getattr(self.pyppeteer_page, name)

    async def query_locator(self, locator: str) -> Optional["ElementHandle"]:
        """Get the element which match ``locator``.

        If no element matches the ``locator``, return ``None``.

        :param str locator: a selector or xpath string
        :return: an element handle or ``None``.
        """
        _type, locator_string = parse_locator(locator)
        if _type == "css":
            return await self.pyppeteer_page.querySelector(locator_string)
        elif _type == "xpath":
            element_list = await self.pyppeteer_page.xpath(locator_string)
            return element_list[0] if element_list else None

    async def waitfor(
        self,
        locator: str,
        visible: bool = True,
        hidden: bool = False,
        timeout: int = 30000,
    ) -> None:
        """Wait until element which matches ``locator``.

        :param str locator: a selector or xpath string.
        :param bool visible: Wait for element to be present in DOM and to be
               visible; i.e. to not have ``display: none`` or ``visibility: hidden``
               CSS properties. Defaults to ``True``.
        :param bool hidden: Wait for element to not be found in the DOM or to
               be hidden, i.e. have ``display: none`` or ``visibility: hidden`` CSS
               properties. Defaults to ``False``.
        :param int timeout: Maximum time to wait for in milliseconds.
               Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :return: None
        :raise ElementTimeoutError: Timeout exceeded while wait for ``locator``.
        """
        _type, locator_string = parse_locator(locator)
        options = {"visible": visible, "hidden": hidden, "timeout": timeout}
        try:
            if _type == "css":
                await self.pyppeteer_page.waitForSelector(
                    locator_string, options=options
                )
            elif _type == "xpath":
                await self.pyppeteer_page.waitForXPath(locator_string, options=options)
        except TimeoutError as e:
            action = "disappear" if hidden else "appear"
            raise ElementTimeoutError(
                locator=locator, timeout=timeout, action=action
            ) from e

    async def type(self, locator: str, text: str, delay: int = 0, clear: bool = False):
        """Focus the element which matches ``locator`` and then
        type text.

        :param locator: a selector or xpath string.
        :param text: what you want to type into.
        :param int delay: specifies time to wait between key presses
               in milliseconds. Defaults to 0.
        :param bool clear: whether to clear existing content befor
               typing. Defaults to ``False``.
        :return:
        """
        element = await self.query_locator(locator)
        if element is None:
            raise ElementNotExistError(locator=locator)
        LOGGER.info('Type text("{}") into element("{}").'.format(text, locator))
        if clear:
            value = await element.executionContext.evaluate(
                "(node => node.value || node.innerText)", element
            )
            if value:
                await _clickable(element)
                await element.click()
                for _ in value:
                    await self.pyppeteer_page.keyboard.press("ArrowRight")
                await self.pyppeteer_page.keyboard.down("Shift")
                for _ in value:
                    await self.pyppeteer_page.keyboard.press("ArrowLeft")
                    await asyncio.sleep(delay / 1000.0)
                await self.pyppeteer_page.keyboard.up("Shift")
                await self.pyppeteer_page.keyboard.press("Backspace")
        await element.type(text, delay=delay)
        await element.dispose()

    async def click(
        self, locator: str, button: str = "left", click_count: int = 1, delay: int = 0,
    ):
        """Click the center of the element which matches ``locator``.

        :param str locator: a selector or xpath string.
        :param str button: ``left``, ``right``, of ``middle``.
               Defaults to ``left``.
        :param int click_count: Defaults to 1.
        :param int delay: Time to wait between ``mousedown`` and
               ``mouseup`` in milliseconds. Defaults to 0.
        :return: None
        :raise ElementNotExistError: if the element which matches
               ``locator`` is not found.
        """
        element = await self.query_locator(locator)
        if element is None:
            raise ElementNotExistError(locator=locator)
        LOGGER.info('Click element("{}").'.format(locator))
        await _clickable(element)
        await element.click(button=button, clickCount=click_count, delay=delay)
        await element.dispose()

    async def get_value(self, locator: str) -> str:
        """Get the element ``value`` or ``innerText`` which matches
        ``locator``.

        :param str locator: a selector or xpath string.
        :return: the element ``value`` or ``innerText`` string.
        :raise ElementNotExistError: if the element which matches
               ``locator`` is not found.
        """
        element = await self.query_locator(locator)
        if element is None:
            raise ElementNotExistError(locator=locator)
        value: str = await element.executionContext.evaluate(
            "(node => node.value || node.innerText)", element
        )
        await element.dispose()
        return value
