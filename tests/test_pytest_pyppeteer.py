async def test_pytest_pyppeteer(pyppeteer):
    page = await pyppeteer.newPage()
    await page.goto("http://www.baidu.com")
