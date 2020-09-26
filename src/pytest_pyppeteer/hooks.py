from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.nodes import Item


async def pytest_pyppeteer_runtest_makereport_call_debug(item: "Item") -> None:
    """Called to add debug information when each of the call(not
    setup/teardown) runtest phases of a test failed item. e.g.
    save screenshot.

    :param Item item: the pytest item object.
    :return: None
    """
