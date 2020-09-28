from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_pyppeteer.models import Browser


async def test_browser(pyppeteer: "Browser"):
    page = await pyppeteer.new_page()
    await page.goto("https://www.baidu.com")
    breakpoint()
    assert 0
