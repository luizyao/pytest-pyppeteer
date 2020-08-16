import asyncio
import inspect
from typing import Dict, Any, Tuple, Union, List, Iterator, Optional
from pathlib import Path

import pytest
import toml
from _pytest import config as conf
from _pytest.fixtures import SubRequest
from _pytest.nodes import Item, Collector
from _pytest.python import PyCollector
from pydantic import root_validator, FilePath
from .models import Page, Pyppeteer, PyppeteerOptions, PyppeteerSettings
from .utils import create_new_pyppeteer_project


def _is_coroutine(obj: Any) -> bool:
    """Check to see if an object is really an asyncio coroutine."""
    return asyncio.iscoroutinefunction(obj) or inspect.isgeneratorfunction(obj)


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
        type=str,
        action="store",
        metavar="path",
        help="Create a new pyppeteer test project in the given path.",
    )


@pytest.mark.tryfirst
def pytest_cmdline_main(config: conf.Config) -> Optional[Union[pytest.ExitCode, int]]:
    nptp: str = config.getoption("nptp")
    if nptp:
        create_new_pyppeteer_project(nptp)
        return pytest.ExitCode.OK


# Mark a hook implementation function such that the plugin machinery will try to call it first/as first as possible.
@pytest.mark.tryfirst
def pytest_pycollect_makeitem(
    collector: PyCollector, name: str, obj: Any
) -> Union[None, Item, Collector, List[Union[Item, Collector]]]:
    """
    Return a custom item/collector for a Python object in a module, or None.

    Stops at first non-None result
    """
    if collector.istestfunction(obj, name) and _is_coroutine(obj):

        def asyncioed_items() -> Iterator[Item]:
            for item in collector._genfunctions(name, obj):
                if "asyncio" not in item.keywords:
                    item.add_marker(pytest.mark.asyncio)
                yield item

        return list(asyncioed_items())


@pytest.fixture(scope="session")
def pyppeteer_settings(pytestconfig: conf.Config) -> Dict[str, Pyppeteer]:
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
    targets = {k: Target.parse_obj(v) for k, v in targets_settings.items()}
    return targets


@pytest.fixture(scope="session")
def target(
    request: SubRequest, pyppeteer_settings: Dict[str, Pyppeteer]
) -> Union[Pyppeteer, Tuple[Pyppeteer]]:
    target_name: Union[str, Tuple[str], List[str]] = request.param
    if isinstance(target_name, (Tuple, List)):
        return tuple([pyppeteer_settings[name] for name in target_name])
    else:
        return pyppeteer_settings[target_name]
