import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pyppeteer.browser import Browser


async def test_pyppeteer(pyppeteer: "Browser"):
    page = await pyppeteer.newPage()
    await page.goto("https://bing.com")


@pytest.mark.options(devtools=True)
async def test_options_mark(pyppeteer):
    page = await pyppeteer.newPage()
    await page.goto("https://bing.com")


async def test_pyppeteer_factory(pyppeteer_factory):
    pyppeteer1 = await pyppeteer_factory()
    pyppeteer2 = await pyppeteer_factory()

    async def _operator1(browser: "Browser"):
        page = await browser.newPage()
        await page.goto("https://bing.com")
        await asyncio.sleep(2)

    async def _operator2(browser: "Browser"):
        page = await browser.newPage()
        await page.goto("https://baidu.com")
        await asyncio.sleep(2)

    await asyncio.gather(_operator1(pyppeteer1), _operator2(pyppeteer2))
