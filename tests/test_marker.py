import asyncio

import pytest


@pytest.mark.options(devtools=True)
async def test_marker(pyppeteer):
    await pyppeteer.new_page()
    await asyncio.sleep(2)
