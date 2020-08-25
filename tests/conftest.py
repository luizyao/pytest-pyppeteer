import asyncio
from pathlib import Path
from typing import Dict

from _pytest.nodes import Item
from pytest_pyppeteer.models import Pyppeteer


async def pytest_pyppeteer_targets_setup(item: Item) -> None:
    targets: Dict[str, Pyppeteer] = item.targets  # type: ignore

    async def setup(target: Pyppeteer):
        await target.open(goto_base_url=True)

    await asyncio.gather(*map(setup, targets.values()))


async def pytest_pyppeteer_targets_teardown(item: Item) -> None:
    targets: Dict[str, Pyppeteer] = item.targets  # type: ignore

    async def teardown(name: str, target: Pyppeteer):
        if item.res_call.failed:
            await asyncio.sleep(2)
            await target.screenshot(path=Path(__file__).parent / "{}.png".format(name))
        await target.close()

    await asyncio.gather(*[teardown(name, target) for name, target in targets.items()])
