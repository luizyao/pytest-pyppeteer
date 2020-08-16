from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest_pyppeteer import models


def test_element_via_empty_parameter():
    with pytest.raises(ValidationError, match="field required"):
        models.Element()


def test_page():
    page = models.Page.parse_obj(
        {
            "search_input": "#kw",
            "search_button": '//*[@id="su"]',
            "results": '(//div[@class="item-root"]//*[@class="title"]/a)[{}]',
        }
    )
    assert page["results"]


def test_page_via_invalid_parameter_format():
    with pytest.raises(
        ValidationError, match="Invalid parameter format, neither a valid css nor xpath"
    ):
        models.Page.parse_obj(
            {"search_input": "#.kw", "search_button": '//*[@id="su"]'}
        )

    with pytest.raises(
        ValidationError, match="Invalid parameter format, neither a valid css nor xpath"
    ):
        models.Page.parse_obj({"search_input": "#kw", "search_button": '//[@id="su"]'})


def test_page_via_invalid_parameter_type():
    with pytest.raises(
        ValidationError, match="Invalid parameter type, string required"
    ):
        models.Page.parse_obj({"search_input": "#kw", "search_button": 123})


def test_options():
    options = {
        "executablePath": Path(__file__),
        "args": ["--lang=en", "--window-size=1200,800"],
        "proxy": [
            "--proxy-server=1.1.1.1:5555,direct://",
            "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
        ],
    }
    pyppeteer_options = models.PyppeteerOptions.parse_obj(options)

    assert pyppeteer_options.args == [
        "--lang=en",
        "--window-size=1200,800",
        "--proxy-server=1.1.1.1:5555,direct://",
        "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
    ]
    assert pyppeteer_options.proxy is None
    assert pyppeteer_options.headless
    assert pyppeteer_options.ignoreHTTPSErrors
    assert pyppeteer_options.slowMo == 1.0
    assert not pyppeteer_options.devtools
    assert not pyppeteer_options.autoClose
    assert pyppeteer_options.defaultViewport == {"width": 1200, "height": 800}


def test_executable_path_non_exist():
    options = {"executablePath": "/path/to/chrome"}

    with pytest.raises(
        ValidationError, match=r"executablePath\n.+type=value_error\.path\.not_exists"
    ):
        models.PyppeteerOptions.parse_obj(options)
