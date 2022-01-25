import pytest

from pytest_pyppeteer.models import Locator


class TestLocator:
    @pytest.mark.parametrize(
        "content, expected_type",
        [
            ("foo", "css"),
            ("foo#bar", "css"),
            ("#bar", "css"),
            ("foo.bar", "css"),
            (".bar", "css"),
            ("//foo", "xpath"),
            ("//foo[@id = 'bar']", "xpath"),
            ("//*[@id = 'bar']", "xpath"),
            ("//foo[@class and contains(concat(' ', normalize-space(@class), ' '), ' bar ')]", "xpath"),
            ("//*[@class and contains(concat(' ', normalize-space(@class), ' '), ' bar ')]", "xpath"),
        ],
    )
    def test_valid_content(self, content, expected_type):
        assert Locator(content)._type == expected_type, "Locator {!r} should be parsed to type {!r}.".format(
            content, expected_type
        )

    @pytest.mark.parametrize("content", ["##foo", "//foo??", "...."])
    def test_invalid_content(self, content):
        with pytest.raises(ValueError, match=content):
            Locator(content)
