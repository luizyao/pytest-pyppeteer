from _pytest.nodes import Item


async def pytest_pyppeteer_targets_setup(item: Item):
    """Called to teardown target before execute a test item."""


async def pytest_pyppeteer_targets_teardown(item: Item):
    """Called to teardown target after execute a test item."""
