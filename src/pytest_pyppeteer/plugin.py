import asyncio
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
import toml
from _pytest import config as conf
from _pytest.config import Config, PytestPluginManager
from _pytest.fixtures import SubRequest
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.runner import CallInfo, TestReport
from pluggy.callers import _Result
from pydantic import root_validator, FilePath

from .models import Page, Pyppeteer, PyppeteerOptions, PyppeteerSettings
from .utils import create_new_pyppeteer_project


def pytest_addhooks(pluginmanager: PytestPluginManager):
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_addoption(
    parser: conf.argparsing.Parser, pluginmanager: conf.PytestPluginManager
) -> None:
    """
    Register argparse-style options and ini-style config values, called once at the beginning of a test run.

    Options can later be accessed through the config object, respectively:

        - **config.getoption(name)** to retrieve the value of a command line option.

        - **config.getini(name)** to retrieve a value read from an ini-style file.

    The config object is passed around on many internal objects via the `.config` attribute or can be retrieved
    as the `pytestconfig` fixture.

    :param parser: To add command line options, call parser.addoption(...).
                    To add ini-file values call parser.addini(...).
    :param pluginmanager: pytest plugin manager, which can be used to install hookspec()’s or hookimpl()’s and
                    allow one plugin to call another plugin’s hooks to change how command line options are added.
    :return: None
    """
    group: conf.argparsing.OptionGroup = parser.getgroup(
        "pyppeteer", "Test with pyppeteer in pytest"
    )
    group.addoption(
        "--nptp",
        "--new-pyppeteer-test-project",
        dest="nptp",
        type=Path,
        action="store",
        metavar="path",
        help="Create a new pyppeteer test project in the given path.",
    )


@pytest.mark.tryfirst
def pytest_cmdline_main(config: conf.Config) -> Optional[Union[pytest.ExitCode, int]]:
    nptp_path: Optional[Path] = config.getoption("nptp")
    if nptp_path:
        create_new_pyppeteer_project(nptp_path)
        return pytest.ExitCode.OK


def _is_coroutine(obj: Any) -> bool:
    """Check to see if an object is really an asyncio coroutine."""
    return asyncio.iscoroutinefunction(obj) or inspect.isgeneratorfunction(obj)


def add_asyncio_marker(item: Item) -> Item:
    if "asyncio" not in item.keywords and _is_coroutine(item.obj):
        item.add_marker(pytest.mark.asyncio)
    return item


# Mark a hook implementation function such that the plugin machinery will try to call it first/as first as possible.
@pytest.mark.tryfirst
def pytest_collection_modifyitems(session: Session, config: Config, items: List[Item]):
    """
    Called after collection has been performed. May filter or re-order the items in-place.

    :param session: The pytest session object.
    :param config: The pytest config object.
    :param items: List of item objects.
    :return:
    """
    items[:] = [add_asyncio_marker(item) for item in items]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo[None]):
    """Add `res_setup` `res_call` `res_teardown` attributes to `Item` to record test result.

    :param Item item:
    :param CallInfo[None] call: The `CallInfo` for the phase.
    :return:
    """
    # Execute all other hooks to obtain the report object
    outcome = yield  # type: _Result
    res: TestReport = outcome.get_result()
    # Set a report attribute for each phase of a call, which can be "setup", "call", "teardown"
    setattr(item, f"res_{res.when}", res)


@pytest.fixture(scope="session")
async def target_factory(pytestconfig: conf.Config) -> Dict[str, Pyppeteer]:
    """The plugin use `[tool.pytest.pyppeteer]` as config item.

    :param pytestconfig: Session-scoped fixture that returns the `_pytest.config.Config` object.
    :return: Configs dictionary object
    """
    configs: Dict = toml.load(str(pytestconfig.inifile))
    settings: Dict = configs.get("tool", {}).get("pytest", {}).get("pyppeteer", None)
    assert settings, '[tool.pytest.pyppeteer] is missing in "pyproject.toml".'

    class Target(Pyppeteer):
        @root_validator(pre=True)
        def merge_custom_parameters(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            name: str = values.get("name")
            values["descpath"] = pytestconfig.rootdir / "desc" / "{}.desc".format(name)
            values["options"] = PyppeteerOptions.parse_obj(settings.get("options", {}))
            values["parameters"] = PyppeteerSettings.parse_obj(
                settings.get("parameters", {})
            )
            return values

        @root_validator
        def pages_must_valid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            descpath: FilePath = values.get("descpath")
            pages_desc = toml.load(descpath)
            values["pages"] = {
                k.lower(): Page.parse_obj(v) for k, v in pages_desc.items()
            }
            return values

        @root_validator
        def homepage_must_exist(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            pages: Dict[str, Page] = values.get("pages")
            try:
                values["page"] = pages["homepage"]
                values["page_name"] = "HomePage"
            except KeyError:
                name: str = values.get("name")
                assert False, "[HomePage] MUST be existed in the {}.desc".format(name)
            return values

    targets_settings: Dict = settings.get("targets", {})
    targets = {
        k: Target.parse_obj(v) for k, v in targets_settings.items() if v.get("name", "")
    }
    yield targets

    await asyncio.gather(
        *pytestconfig.hook.pytest_pyppeteer_all_targets_teardown(
            targets=targets.values()
        )
    )


@pytest.fixture
async def target(
    request: SubRequest, pytestconfig: conf.Config, target_factory: Dict[str, Pyppeteer]
) -> Union[Pyppeteer, Tuple[Pyppeteer]]:
    targets_name = (request.param,) if isinstance(request.param, str) else request.param
    targets_used: Tuple[Pyppeteer] = tuple(
        target_factory[name] for name in targets_name
    )
    setattr(request.node, "targets", dict(zip(targets_name, targets_used)))

    await asyncio.gather(
        *pytestconfig.hook.pytest_pyppeteer_targets_setup(item=request.node)
    )

    yield targets_used[0] if len(targets_used) == 1 else targets_used

    await asyncio.gather(
        *pytestconfig.hook.pytest_pyppeteer_targets_teardown(item=request.node)
    )


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for each test case.
    @return:
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
