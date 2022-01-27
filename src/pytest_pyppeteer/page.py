# flake8: noqa
from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING

import cssselect
from lxml import etree
from pyppeteer.errors import ElementHandleError

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

if TYPE_CHECKING:
    from typing import Optional

    from pyppeteer.element_handle import ElementHandle
    from pyppeteer.page import Page

logger = getLogger("pytest_pyppeteer.page")


def _parse_locator(css_or_xpath: str) -> tuple:
    if not isinstance(css_or_xpath, str):
        raise TypeError("Locator {!r} is not a string.".format(css_or_xpath))

    try:
        cssselect.parse(css_or_xpath)
    except cssselect.SelectorSyntaxError:
        pass
    else:
        return "css", css_or_xpath

    try:
        etree.XPath(css_or_xpath)
    except etree.XPathSyntaxError:
        pass
    else:
        return "xpath", css_or_xpath

    raise ValueError("Locator {!r} neither a css nor an xpath string.".format(css_or_xpath))


async def query_locator(self: Page, css_or_xpath: str) -> Optional[ElementHandle]:
    _type, css_or_xpath = _parse_locator(css_or_xpath)
    if _type == "css":
        return await self.querySelector(css_or_xpath)
    elif _type == "xpath":
        elements = await self.xpath(css_or_xpath)
        return elements[0] if elements else None


async def waitfor(
    self: Page, css_or_xpath: str, visible: bool = True, hidden: bool = False, timeout: int = 30000
) -> None:
    """Wait for an element visible or hidden.

    Args:
        css_or_xpath (str): CSS or XPath string.
        visible (bool, optional): Waiting for visible. Defaults to True.
        hidden (bool, optional): Waiting for hidden. Defaults to False.
        timeout (int, optional): Timeout in microsecond. Defaults to 30000.
    """
    _type, css_or_xpath = _parse_locator(css_or_xpath)
    options = {"visible": visible, "hidden": hidden, "timeout": timeout}
    logger.debug("Wait for element {!r} {!r}.".format(css_or_xpath, options))
    if _type == "css":
        await self.waitForSelector(css_or_xpath, options=options)
    elif _type == "xpath":
        await self.waitForXPath(css_or_xpath, options=options)


async def click(
    self: Page,
    css_or_xpath: str,
    button: Literal["left", "right", "middle"] = "left",
    click_count: int = 1,
    delay: int = 0,
):
    """Click an element.

    Args:
        css_or_xpath (str): CSS or XPath string.
        button (Literal["left", "right", "middle"], optional): Which mouse button to click with. Defaults to "left".
        click_count (int, optional): How many clicks. Defaults to 1.
        delay (int, optional): Time to wait between ``mousedown`` and ``mouseup`` event in milliseconds. Defaults to 0.
    """
    element: Optional[ElementHandle] = await self.query_locator(css_or_xpath)
    if element is None:
        logger.error("Element {!r} does not exist.".format(css_or_xpath))
    else:
        for _ in range(10):
            try:
                await element._clickablePoint()
            except ElementHandleError as error:
                logger.debug(
                    "Element {!r} is not clickable because of {}, waiting... and try again.".format(css_or_xpath, error)
                )
                await asyncio.sleep(0.5)
            else:
                logger.debug("Click element {!r}".format(css_or_xpath))
                await element.click(button=button, clickCount=click_count, delay=delay)
                await element.dispose()
                break


async def type(self: Page, css_or_xpath: str, text: str, delay: int = 0, clear: bool = False):
    """Type some text in the element input.

    Args:
        css_or_xpath (str): CSS or XPath string.
        text (str): Type what.
        delay (int, optional): Time to wait between each input event in milliseconds. Defaults to 0.
        clear (bool, optional): Whether to clear original content. Defaults to False.
    """
    element: Optional[ElementHandle] = await self.query_locator(css_or_xpath)
    if element is None:
        logger.error("Element {!r} does not exist.".format(css_or_xpath))
    else:
        logger.debug("Type text {!r} into element {!r}.".format(text, css_or_xpath))
        if clear:
            value = await element.executionContext.evaluate("(node => node.value || node.innerText)", element)
            if value:
                await element.click()
                for _ in value:
                    await self.keyboard.press("ArrowRight")
                await self.keyboard.down("Shift")
                for _ in value:
                    await self.keyboard.press("ArrowLeft")
                    await asyncio.sleep(delay / 1000.0)
                await self.keyboard.up("Shift")
                await self.keyboard.press("Backspace")
        await element.type(text, delay=delay)
        await element.dispose()


async def get_value(self: Page, css_or_xpath: str) -> Optional[str]:
    """Get an element value.

    Args:
        css_or_xpath (str): CSS or XPath string.

    Returns:
        Optional[str]: The element value.
    """
    element: Optional[ElementHandle] = await self.query_locator(css_or_xpath)
    if element is None:
        logger.error("Element {!r} does not exist.".format(css_or_xpath))
    else:
        value: str = await element.executionContext.evaluate("(node => node.value || node.innerText)", element)
        await element.dispose()
        return value
