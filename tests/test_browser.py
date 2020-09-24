from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_pyppeteer.models import Browser


async def test_browser(pyppeteer: "Browser"):
    page = await pyppeteer.new_page()
    await page.goto("http://192.168.1.9:8080")
    element = await page.query_locator(
        ".login-card-form > div:nth-of-type(1) fieldset input"
    )
    await element.type("admin")
    breakpoint()
