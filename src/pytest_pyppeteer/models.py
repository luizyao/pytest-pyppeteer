"""
How to model a page?
"""
from typing import List, Dict, Any, Union, Optional

import cssselect
from lxml import etree
from pydantic import BaseModel, root_validator, FilePath, HttpUrl
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Response
from pyppeteer.page import Page as Tab


class Locator(str):
    @classmethod
    def __get_validators__(cls):
        """
        One or more validators may be yielded which will be called in the
        order to validate the input, each validator will receive as an input
        the value returned from the previous validator

        :return:
        """
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        """Locator string must a valid css or xpath.

        :param value: a locator string
        :return:
        """
        if not isinstance(value, str):
            raise TypeError("Invalid parameter type, string required.")
        if "{}" in value:
            return cls(
                value
            )  # TODO: Custom parameters need to be dynamically populated in use
        # CSS
        try:
            cssselect.parse(value)
        except cssselect.SelectorSyntaxError:
            pass
        else:
            return cls(value)
        # XPath
        try:
            etree.XPath(value)
        except etree.XPathSyntaxError:
            pass
        else:
            return cls(value)
        raise ValueError("Invalid parameter format, neither a valid css nor xpath.")

    def __repr__(self):
        return "Locator({})".format(super().__repr__())


class Element(BaseModel):
    __root__: Locator


class Page(BaseModel):
    __root__: Dict[str, Union[Element]]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


class PyppeteerOptions(BaseModel):
    # Whether to ignore HTTPS errors.
    ignoreHTTPSErrors: bool = True
    # Whether to run browser in headless mode.
    headless: bool = True
    # Path to a Chromium or Chrome executable to run instead of default bundled Chromium.
    executablePath: FilePath = None
    # Slow down pyppeteer operations by the specified amount of milliseconds.
    slowMo: float = 1.0
    # Set a consistent viewport for each page.
    defaultViewport: Dict[str, int] = {"width": 1200, "height": 800}
    args: List[str] = ["--lang=en", "--window-size=1200,800"]
    # Whether to auto-open a DevTools panel for each tab.
    # If this option is True, the `headless` option will be set False.
    devtools: bool = False
    # Automatically close browser process when script completed.
    autoClose: bool = False

    # https://source.chromium.org/chromium/chromium/src/+/master:net/docs/proxy.md
    # ['--proxy-server=10.40.4.183:6000,direct://', ' --proxy-bypass-list=192.0.0.1/8;10.40.0.1/16']
    proxy: List[str] = None

    @root_validator(pre=True)
    def use_proxy(cls, values: Dict[str, Any]):
        proxy: List[str] = values.get("proxy")
        if proxy is not None:
            values["args"].extend(proxy)
            values["proxy"] = None
        return values


class PyppeteerSettings(BaseModel):
    # The default maximum navigation timeout in milliseconds.
    # This parameter changes the default timeout of 30 seconds for the following methods:
    #   * :meth:`goto`
    #   * :meth:`goBack`
    #   * :meth:`goForward`
    #   * :meth:`reload`
    #   * :meth:`waitForNavigation`
    default_navigation_timeout: int = 90000


class Pyppeteer(BaseModel):
    name: str
    base_url: Optional[HttpUrl] = None
    descpath: Optional[FilePath] = None
    pages: Dict[str, Page] = {}
    page: Optional[Page] = None
    page_name: str = ""
    options: Optional[PyppeteerOptions] = None
    parameters: Optional[PyppeteerSettings] = None
    browser: Optional[Browser] = None
    tab: Optional[Tab] = None

    class Config:
        arbitrary_types_allowed = True

    async def open(self, goto_base_url: bool = False) -> None:
        """Open a new browser tab. If browser instance is not exists, open browser first.

        :type goto_base_url: Whether goto `base_url` directly. 'base_url' defined in the `pyproject`
                            in the `rootdir` directory.
        :return:
        """
        if self.browser is None:
            self.browser = await launch(options=self.options.dict(exclude_none=True))
        self.tab = await self.browser.newPage()
        self.tab.setDefaultNavigationTimeout(self.parameters.default_navigation_timeout)
        if goto_base_url:
            await self.goto(self.base_url)
            self.switch_page("HomePage")

    def switch_page(self, page_name: str) -> None:
        try:
            self.page = self.pages[page_name.lower()]
            self.page_name = page_name
        except KeyError:
            assert False, "[{}] is missing in the {}.desc.".format(page_name, self.name)

    def _get_element_locator(self, name: str, custom_parameter: tuple = ()) -> str:
        try:
            return self.page[name].__root__.format(*custom_parameter)
        except KeyError:
            assert False, 'No such element("{}") in the page([{}]).'.format(
                name, self.page_name
            )

    async def wait_for_navigation(
        self, timeout: int = 30000, wait_until: Union[str, List[str]] = "load"
    ) -> Response:
        """Wait for navigation.

        Available options are same as :meth:`goto` method.

        This returns :class:`~pyppeteer.network_manager.Response` when the page
        navigates to a new URL or reloads. It is useful for when you run code
        which will indirectly cause the page to navigate. In case of navigation
        to a different anchor or navigation due to
        `History API <https://developer.mozilla.org/en-US/docs/Web/API/History_API>`_
        usage, the navigation will return ``None``.

        Consider this example:

        .. code::

            navigation_promise = async.ensure_future(tab.wait_for_navigation())
            await tab.click('a.my-link')  # indirectly cause a navigation
            await navigation_promise  # wait until navigation finishes

        or,

        .. code::

            await asyncio.wait([
                tab.click('a.my-link'),
                tab.wait_for_navigation(),
            ])

        .. note::
            Usage of the History API to change the URL is considered a
            navigation.

        :param timeout: Maximum navigation time in milliseconds, defaults to 30 seconds,
                        pass `0` to disable timeout. The default value can be changed by using
                        the :meth:`setDefaultNavigationTimeout` method.
        :param wait_until: When to consider navigation succeeded, defaults to `load`. Given a
                        list of event strings, navigation is considered to be successful after
                        all events have been fired. Events can be either:
                            * `load`: when `load` event is fired.
                            * `domcontentloaded`: when the `DOMContentLoaded` event is fired.
                            * `networkidle0`: when there are no more than 0 network connections
                                for at least 500 ms.
                            * `networkidle2`: when there are no more than 2 network connections
                                for at least 500 ms.
        :return:
        """
        return await self.tab.waitForNavigation(timeout=timeout, waitUntil=wait_until)

    async def wait_for_element(
        self,
        elem_name: str,
        visible: bool = True,
        hidden: bool = False,
        timeout: Union[float, int] = 30000,
        custom_parameter: tuple = (),
    ):
        """Wait until element which matches ``elem_name`` appears on page.

        Wait for the ``elem_name`` to appear in page. If at the moment of
        calling the method the ``elem_name`` already exists, the method will
        return immediately. If the selector doesn't appear after the
        ``timeout`` milliseconds of waiting, the function will raise error.

        :param elem_name: Element name.
        :param visible: Wait for element to be present in DOM and to be visible;
                        i.e. to not have ``display: none`` or ``visibility: hidden``
                        CSS properties. Defaults to ``True``.
        :param hidden: Wait for element to not be found in the DOM or to be hidden;
                        i.e. have ``display: none`` or ``visibility: hidden`` CSS
                        properties. Defaults to ``False``.
        :param timeout: Maximum time to wait for in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param custom_parameter: The values used to replace "%" in the locator.
        :return:
        """
        locator: str = self._get_element_locator(elem_name, custom_parameter)
        await self.tab.waitForSelector(
            selector=locator, visible=visible, hidden=hidden, timeout=timeout
        )

    async def input(
        self,
        elem_name: str,
        text: str,
        clear: bool = False,
        delay: int = 0,
        timeout: Union[float, int] = 30000,
        custom_parameter: tuple = (),
    ) -> None:
        """Input ``text`` on the element which matches ``elem_name``.

        :param elem_name: Element name
        :param text: A text to input into a focused element.
        :param clear: Clear the input field first. Defaults to True.
        :param delay: Time to wait between key presses in milliseconds. Defaults to 0.
        :param timeout: Maximum time to wait for in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param custom_parameter: The values used to replace "%" in the locator.
        :return:
        """
        await self.wait_for_element(
            elem_name, visible=True, timeout=timeout, custom_parameter=custom_parameter
        )
        locator: str = self._get_element_locator(elem_name, custom_parameter)
        if clear:
            value = await self.get_value(elem_name)
            if value:
                from asyncio import sleep

                await self.click(elem_name)
                await self.tab.keyboard.down("Shift")
                for _ in value:
                    await self.tab.keyboard.press("ArrowLeft")
                    await sleep(delay / 1000.0)
                await self.tab.keyboard.up("Shift")
                await self.tab.keyboard.press("Backspace")
        await self.tab.type(selector=locator, text=text, delay=delay)

    async def click(
        self,
        elem_name: str,
        button: str = "left",
        click_count: int = 1,
        delay: Union[float, int] = 0,
        custom_parameter: tuple = (),
        timeout: Union[float, int] = 30000,
    ) -> None:
        """Click element which matches ``elem_name``.

        This method fetches an element with ``elem_name``, scrolls it into view
        if needed, and then uses :attr:`mouse` to click in the center of the
        element. If there's no element matching ``elem_name``, the method raises
        ``PageError``.

        .. note:: If this method triggers a navigation event and there's a
            separate :meth:`waitForNavigation`, you may end up with a race
            condition that yields unexpected results. The correct pattern for
            click and wait for navigation is the following::

                await asyncio.wait([
                    tab.click('a.my-link'),
                    tab.wait_for_navigation(),
                ])

        :param elem_name:
        :param button: ``left``, ``right``, or ``middle``. Defaults to ``left``.
        :param click_count: Defaults to 1.
        :param delay: Time to wait between ``mousedown`` and ``mouseup`` in milliseconds. Defaults to 0.
        :param custom_parameter: The values used to replace "%" in the locator.
        :param timeout: Maximum time to wait for in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :return: None
        """
        await self.wait_for_element(
            elem_name, visible=True, timeout=timeout, custom_parameter=custom_parameter
        )
        locator: str = self._get_element_locator(elem_name, custom_parameter)
        await self.tab.click(
            selector=locator, clickCount=click_count, button=button, delay=delay,
        )

    async def get_value(
        self,
        elem_name: str,
        custom_parameter: tuple = (),
        timeout: Union[float, int] = 30000,
    ) -> str:
        """Get value with an element which matches ``elem_name``.

        This method raises error if no element matched the ``elem_name``.

        :param elem_name: Element name.
        :param custom_parameter: The values used to replace "%" in the locator.
        :param timeout: Maximum time to wait for in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :return:
        """
        await self.wait_for_element(
            elem_name, visible=True, timeout=timeout, custom_parameter=custom_parameter
        )
        locator: str = self._get_element_locator(elem_name, custom_parameter)
        value: str = await self.tab.querySelectorEval(
            locator, "(node => node.value || node.innerText)"
        )
        return value.strip()

    async def goto(
        self, url: str, timeout: int = 30000, wait_until: Union[str, List[str]] = "load"
    ) -> None:
        """Go to the `url`.

        The `Page.goto` will raise errors if:

        * there's an SSL error (e.g. in case of self-signed certificates)
        * target URL is invalid
        * the `timeout` is exceeded during navigation
        * then main resource failed to load

        .. note::
            :meth:`goto` either raise error or return a main resource response.
            The only exceptions are navigation to `about:blank` or navigation
            to the same URL with a different hash, which would succeed and
            return `None`.

        .. note::
            Headless mode doesn't support navigation to a PDF document.

        :param url: URL to navigate page to. The url should include scheme, e.g. `https://`.
        :param timeout: Maximum navigation time in milliseconds, defaults to 30 seconds,
                        pass `0` to disable timeout. The default value can be changed by using
                        the :meth:`setDefaultNavigationTimeout` method.
        :param wait_until: When to consider navigation succeeded, defaults to `load`. Given a
                        list of event strings, navigation is considered to be successful after
                        all events have been fired. Events can be either:
                            * `load`: when `load` event is fired.
                            * `domcontentloaded`: when the `DOMContentLoaded` event is fired.
                            * `networkidle0`: when there are no more than 0 network connections
                                for at least 500 ms.
                            * `networkidle2`: when there are no more than 2 network connections
                                for at least 500 ms.
        :return: None
        """
        await self.tab.goto(url, timeout=timeout, waitUntil=wait_until)

    async def close(self) -> None:
        """Close browser.

        :return:
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
