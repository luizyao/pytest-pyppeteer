from dataclasses import dataclass


@dataclass(init=False)
class Elements:
    url = "https://movie.douban.com/"

    query = "#inp-query"
    apply = ".inp-btn > input:nth-child(1)"

    result = (
        "#root > div > div > div > div > div:nth-child(1) > div.item-root a.cover-link"
    )
    rating = (
        "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong"
    )


async def test_options_mark(pyppeteer):
    page = await pyppeteer.new_page()
    await page.goto("https://movie.douban.com")

    await page.type(Elements.query, "The Shawshank Redemption")
    await page.click(Elements.apply)

    await page.waitfor(Elements.result)
    await page.click(Elements.result)

    await page.waitfor(Elements.rating)
    rating = await page.get_value(Elements.rating)
    assert float(rating) >= 9.0
