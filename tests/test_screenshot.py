import base64
from pathlib import Path

import pytest
from pytest_pyppeteer.models import Pyppeteer


@pytest.mark.parametrize("target", ["target1", "target2"], indirect=True)
async def test_screenshot(target: Pyppeteer):
    path_binary = Path(__file__).parent / "screenshot_binary.png"
    path_base64 = Path(__file__).parent / "screenshot_base64.png"
    path_binary.unlink(missing_ok=True)
    path_base64.unlink(missing_ok=True)

    await target.screenshot(path_binary)
    assert path_binary.is_file()
    screenshot_base64 = await target.screenshot(
        full_page=True, encoding="base64", omit_background=True
    )
    with path_base64.open("wb") as f:
        f.write(base64.b64decode(screenshot_base64))
    assert path_base64.is_file()
    path_binary.unlink(missing_ok=True)
    path_base64.unlink(missing_ok=True)
