from pathlib import Path


def create_new_pyppeteer_project(nptp: Path) -> None:
    path: Path = Path(nptp)
    desc_dir: Path = path / "desc"
    desc_dir.mkdir(parents=True, exist_ok=True)

    with open(path / "pyproject.toml", mode="w") as f:
        f.write(
            """# https://docs.pytest.org/en/stable/customize.html#pyproject-toml
[tool.pytest.ini_options]

# pytest-pyppeteer configs
[tool.pytest.pyppeteer]

[tool.pytest.pyppeteer.targets]
[tool.pytest.pyppeteer.targets.target1]
name = ""
base_url = ""

[tool.pytest.pyppeteer.targets.target2]
name = ""
base_url = ""

[tool.pytest.pyppeteer.parameters]
# The default maximum navigation timeout in milliseconds.
# This parameter changes the default timeout of 30 seconds for the following methods:
#   * :meth:`goto`
#   * :meth:`goBack`
#   * :meth:`goForward`
#   * :meth:`reload`
#   * :meth:`waitForNavigation`
default_navigation_timeout = 90000.0

[tool.pytest.pyppeteer.options]
# Whether to ignore HTTPS errors.
ignoreHTTPSErrors = true
# Whether to run browser in headless mode.
headless = false

# Path to a Chromium or Chrome executable.
# executablePath = "/Applications/Chrome.app/Contents/MacOS/Google Chrome"

# Slow down pyppeteer operations by the specified amount of milliseconds.
slowMo = 1.0

# Set a consistent viewport for each page.
defaultViewport = { width = 1200, height = 800 }

args = ['--lang=en', '--window-size=1200,800']
# https://source.chromium.org/chromium/chromium/src/+/master:net/docs/proxy.md
# proxy = ['--proxy-server=1.1.1.1:5555,direct://', '--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8']

# Whether to auto-open a DevTools panel for each tab.
# If this option is True, the `headless` option will be set False.
devtools = false

# Automatically close browser process when script completed.
autoClose = false
"""
        )

    with open(path / "test_{}.py".format(path.name), mode="w") as f:
        f.write(
            """import pytest
from pytest_pyppeteer.models import Pyppeteer


@pytest.mark.parametrize("target", [("target1", "target2")], indirect=True)
async def test_{}(target):
    pass
""".format(
                path.name
            )
        )
