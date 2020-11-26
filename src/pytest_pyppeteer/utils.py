import sys
from pathlib import Path

import cssselect
from lxml import etree

from pytest_pyppeteer.errors import LocatorNotAValidSelectorOrXPathError

CHROME_EXECUTABLE = {
    "mac": Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    "win64": Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    "win32": Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
}


def current_platform() -> str:
    """Return current platform name.

    :return: the platform name. only be one of ``mac`` ``win64`` ``win32``.
    :raise OSError: if current platform is not supported.
    """
    if sys.platform.startswith("darwin"):
        return "mac"
    if sys.platform.startswith("win"):
        if sys.maxsize > 2 ** 31 - 1:
            return "win64"
        return "win32"
    raise OSError(
        'Unsupported platform: "{}"; Now only support "win64", "win32", "mac"'.format(
            sys.platform
        )
    )


def parse_locator(locator: str) -> tuple:
    """validate that the locator string must a valid css or
    xpath.

    :param locator: a locator string.
    :return: a tuple contains locator_type and locator_string.
    :raise LocatorNotAValidSelectorOrXPath: locator is not a
           valid selector or xpath string.
    """
    if not isinstance(locator, str):
        raise TypeError("Locator not a string.")
    # CSS selector
    try:
        cssselect.parse(locator)
    except cssselect.SelectorSyntaxError:
        pass
    else:
        return "css", locator
    # XPath
    try:
        etree.XPath(locator)
    except etree.XPathSyntaxError:
        pass
    else:
        return "xpath", locator
    raise LocatorNotAValidSelectorOrXPathError(locator=locator)
