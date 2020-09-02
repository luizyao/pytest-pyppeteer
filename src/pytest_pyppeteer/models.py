"""
How to model a page?
"""
import asyncio
from functools import partial
from typing import List, Dict, Any, Union, Optional, Tuple, Awaitable

import cssselect
from lxml import etree
from pydantic import BaseModel, root_validator, FilePath, HttpUrl
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.element_handle import ElementHandle
from pyppeteer.network_manager import Response
from pyppeteer.page import Page as Tab


class Locator(tuple):
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
    def validate(cls, value: str) -> tuple:
        """Locator string must a valid css or xpath.

        :param value: a locator string
        :return:
        """
        if not isinstance(value, str):
            raise TypeError("Invalid parameter type, string required.")
        simulated_value = value.replace("{}", "1")
        # CSS selector
        try:
            cssselect.parse(simulated_value)
        except cssselect.SelectorSyntaxError:
            pass
        else:
            return "CSS", value
        # XPath
        try:
            etree.XPath(simulated_value)
        except etree.XPathSyntaxError:
            pass
        else:
            return "XPath", value
        raise ValueError("Invalid parameter format, neither a valid css nor xpath.")

    def __repr__(self):
        return "::".join(super(Locator, self).__repr__())


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
    tabs: List[Tab] = list()

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
            self.tabs = await self.browser.pages()
        try:
            self.tab = self.tabs[0]
            self.tab.setDefaultNavigationTimeout(
                self.parameters.default_navigation_timeout
            )
        except IndexError:
            await self.new_page()
        if goto_base_url:
            await self.goto(self.base_url)
            self.switch_page("HomePage")

    async def new_page(self):
        if self.browser is None:
            raise ValueError("Open a browser first.")
        self.tab = await self.browser.newPage()
        self.tab.setDefaultNavigationTimeout(self.parameters.default_navigation_timeout)
        self.tabs.append(self.tab)

    def switch_page(self, page_name: str) -> None:
        try:
            self.page = self.pages[page_name.lower()]
            self.page_name = page_name
        except KeyError:
            assert False, "[{}] is missing in the {}.desc.".format(page_name, self.name)

    def _get_element_locator(
        self, name: str, custom_parameter: Union[Tuple[Any], Any] = ()
    ) -> Tuple[str, str]:
        try:
            css_or_xpath, locator = self.page[name].__root__
            if not isinstance(custom_parameter, tuple):
                custom_parameter = (custom_parameter,)
            return css_or_xpath, locator.format(*custom_parameter)
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

    async def wait_for_css_or_xpath(
        self,
        css_or_xpath: str,
        locator_string: str,
        visible: bool = True,
        hidden: bool = False,
        timeout: Union[float, int] = 30000,
    ) -> Awaitable:
        """Wait until element which matches ``locator_string`` appears on page by ``xpath_or_css``.

        If at the moment of calling the method the ``locator_string`` already exists, the method will
        return immediately. If the selector doesn't appear after the ``timeout`` milliseconds of waiting,
        the function will raise error.

        :param css_or_xpath: Locator method. Only could be `css` or `xpath`.
        :param locator_string: Locator string.
        :param visible: Wait for element to be present in DOM and to be visible;
                        i.e. to not have ``display: none`` or ``visibility: hidden``
                        CSS properties. Defaults to ``True``.
        :param hidden: Wait for element to not be found in the DOM or to be hidden;
                        i.e. have ``display: none`` or ``visibility: hidden`` CSS
                        properties. Defaults to ``False``.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :return: Return awaitable object which resolves when element specified
                 by element name is added to DOM.
        """
        assert css_or_xpath.lower() in (
            "css",
            "xpath",
        ), "Only support xpath and css locator."
        if css_or_xpath.lower() == "css":
            return await self.tab.waitForSelector(
                selector=locator_string, visible=visible, hidden=hidden, timeout=timeout
            )
        elif css_or_xpath.lower() == "xpath":
            return await self.tab.waitForXPath(
                xpath=locator_string, visible=visible, hidden=hidden, timeout=timeout
            )

    async def query_element(
        self,
        elem_name: str,
        visible: bool = True,
        hidden: bool = False,
        timeout: Union[float, int] = 30000,
        custom_parameter: Union[Tuple[Any], Any] = (),
    ) -> Optional[ElementHandle]:
        css_or_xpath, locator = self._get_element_locator(elem_name, custom_parameter)
        await self.wait_for_css_or_xpath(
            css_or_xpath, locator, visible=visible, hidden=hidden, timeout=timeout
        )

        element: Optional[ElementHandle] = None
        if css_or_xpath.lower() == "css":
            element = await self.tab.querySelector(selector=locator)
        elif css_or_xpath.lower() == "xpath":
            element = (await self.tab.xpath(expression=locator))[0]
        return element

    async def query_elements(
        self,
        elem_name: str,
        visible: bool = True,
        hidden: bool = False,
        timeout: Union[float, int] = 30000,
        custom_parameter: Union[Tuple[Any], Any] = (),
    ) -> List[Optional[ElementHandle]]:
        css_or_xpath, locator = self._get_element_locator(elem_name, custom_parameter)
        await self.wait_for_css_or_xpath(
            css_or_xpath, locator, visible=visible, hidden=hidden, timeout=timeout
        )

        elements: List[Optional[ElementHandle]] = list()
        if css_or_xpath.lower() == "css":
            elements = await self.tab.querySelectorAll(selector=locator)
        elif css_or_xpath.lower() == "xpath":
            elements = await self.tab.xpath(expression=locator)
        return elements

    async def input(
        self,
        element: Union[str, ElementHandle],
        text: str,
        clear: bool = False,
        delay: int = 0,
        timeout: Union[float, int] = 30000,
        custom_parameter: Union[Tuple[Any], Any] = (),
    ) -> None:
        """Input ``text`` on the element which matches ``elem_name``.

        :param element: Element name or an element.
        :param text: A text to input into a focused element.
        :param clear: Clear the input field first. Defaults to True.
        :param delay: Time to wait between key presses in milliseconds. Defaults to 0.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param custom_parameter: The values used to replace "{}" in the locator.
        :return:
        """
        if isinstance(element, str):
            element: ElementHandle = await self.query_element(
                element,
                visible=True,
                timeout=timeout,
                custom_parameter=custom_parameter,
            )
        if clear:
            value = await self.get_value(element, dispose=False)
            if value:
                await self.click(element, dispose=False)
                for _ in value:
                    await self.tab.keyboard.press("ArrowRight")
                await self.tab.keyboard.down("Shift")
                for _ in value:
                    await self.tab.keyboard.press("ArrowLeft")
                    await asyncio.sleep(delay / 1000.0)
                await self.tab.keyboard.up("Shift")
                await self.tab.keyboard.press("Backspace")
        await element.type(text, delay=delay)
        await element.dispose()

    async def click(
        self,
        element: Union[str, ElementHandle],
        button: str = "left",
        click_count: int = 1,
        hold: Union[float, int] = 0,
        custom_parameter: Union[Tuple[Any], Any] = (),
        timeout: Union[float, int] = 30000,
        dispose: bool = True,
        delay: Union[float, int] = 0,
    ) -> None:
        """Click element which matches ``elem_name`` or ``element``.

        Scrolls it into view if needed, and then uses :attr:`mouse` to click in the center of the
        element. If there's no element matching ``elem_name``, the method raises ``PageError``.

        .. note:: If this method triggers a navigation event and there's a
            separate :meth:`waitForNavigation`, you may end up with a race
            condition that yields unexpected results. The correct pattern for
            click and wait for navigation is the following::

                await asyncio.wait([
                    tab.click('a.my-link'),
                    tab.wait_for_navigation(),
                ])

        :param element: Element name or an element.
        :param button: ``left``, ``right``, or ``middle``. Defaults to ``left``.
        :param click_count: Defaults to 1.
        :param hold: Time to wait between ``mousedown`` and ``mouseup`` in milliseconds. Defaults to 0.
        :param custom_parameter: The values used to replace "{}" in the locator.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param dispose: Whether to dispose element handler.
        :param delay: Time to wait between find and click elements in milliseconds. Defaults to 0.
        :return: None
        """
        if isinstance(element, str):
            element: ElementHandle = await self.query_element(
                element,
                visible=True,
                timeout=timeout,
                custom_parameter=custom_parameter,
            )
        await asyncio.sleep(delay / 1000.0)
        await element.click(clickCount=click_count, button=button, delay=hold)
        if dispose:
            await element.dispose()

    async def get_value(
        self,
        element: Union[str, ElementHandle],
        custom_parameter: Union[Tuple[Any], Any] = (),
        timeout: Union[float, int] = 30000,
        dispose: bool = True,
    ) -> str:
        """Get value with an element which matches ``elem_name`` or ``element``.

        This method raises error if no element matched the ``elem_name``.

        :param element: Element name or an element.
        :param custom_parameter: The values used to replace "{}" in the locator.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param dispose: Whether to dispose element handler.
        :return:
        """
        if isinstance(element, str):
            element: ElementHandle = await self.query_element(
                element,
                visible=True,
                timeout=timeout,
                custom_parameter=custom_parameter,
            )
        value: str = await element.executionContext.evaluate(
            "(node => node.value || node.innerText)", element
        )
        if dispose:
            await element.dispose()
        return value.strip()

    async def get_values(
        self,
        element_name: str,
        custom_parameter: Union[Tuple[Any], Any] = (),
        timeout: Union[float, int] = 30000,
        dispose: bool = True,
    ) -> List[str]:
        """Get value of each element found by ``element_name``.

        This method raises error if no element matched the ``elem_name``.

        :param element_name: Element name
        :param custom_parameter: The values used to replace "{}" in the locator.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param dispose: Whether to dispose element handler.
        :return:
        """
        elements: List[ElementHandle] = await self.query_elements(
            element_name,
            visible=True,
            timeout=timeout,
            custom_parameter=custom_parameter,
        )
        get_element_value = partial(
            self.get_value,
            custom_parameter=custom_parameter,
            timeout=timeout,
            dispose=dispose,
        )
        values: List[str] = await asyncio.gather(*map(get_element_value, elements))
        return values

    async def hover(
        self,
        element: Union[str, ElementHandle],
        custom_parameter: Union[Tuple[Any], Any] = (),
        timeout: Union[float, int] = 30000,
        delay: Union[float, int] = 0,
        dispose: bool = True,
    ) -> None:
        """Move mouse over to center of the element which matches ``elem_name``.

        If needed, this method scrolls element into view. If this element is
        detached from DOM tree, the method raises an ``ElementHandleError``.

        If no element matched the ``elem_name``, raise ``PageError``.

        :param element: Element name or an element.
        :param custom_parameter: The values used to replace "{}" in the locator.
        :param timeout: Maximum time to wait for searching element in milliseconds.
                        Defaults to 30000 (30 seconds). Pass ``0`` to disable timeout.
        :param delay: The hover time on this element to delay the next operation in milliseconds.
        :param dispose: Whether to dispose element handler.
        :return:
        """
        if isinstance(element, str):
            element: ElementHandle = await self.query_element(
                element,
                visible=True,
                timeout=timeout,
                custom_parameter=custom_parameter,
            )
        await element.hover()
        await asyncio.sleep(delay / 1000)
        if dispose:
            await element.dispose()

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

    async def screenshot(
        self,
        path: str = None,
        type_: str = "png",
        full_page: bool = False,
        clip: Dict[str, int] = None,
        omit_background: bool = False,
        encoding: str = "binary",
    ) -> Union[bytes, str]:
        """Take a screenshot.

        :param path: The file path to save the image to. The screenshot type
                    will be inferred from the file extension.
        :param type_: Specify screenshot type, can be either ``jpeg`` or
                    ``png``. Defaults to ``png``.
        :param full_page: When true, take a screenshot of the full scrollable
                    page. Defaults to ``False``.
        :param clip: An object which specifies clipping region of the page.
                    This option should have the following fields:
                        * ``x`` (int): x-coordinate of top-left corner of clip area.
                        * ``y`` (int): y-coordinate of top-left corner of clip area.
                        * ``width`` (int): width of clipping area.
                        * ``height`` (int): height of clipping area.
        :param omit_background: Hide default white background and allow capturing
                    screenshot with transparency. Defaults to ``False``.
        :param encoding: The encoding of the image, can be either ``'base64'`` or
                    ``'binary'``. Defaults to ``'binary'``.
        """
        return await self.tab.screenshot(
            options={"type": type_},
            path=path,
            fullPage=full_page,
            clip=clip,
            omitBackground=omit_background,
            encoding=encoding,
        )

    async def close(self) -> None:
        """Close browser.

        :return:
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
