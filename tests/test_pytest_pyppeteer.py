import pytest
from _pytest.pytester import Pytester

from pytest_pyppeteer.page import Locator


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
def test_locator_valid_content(content, expected_type):
    assert Locator(content)._type == expected_type, "Locator {!r} should be parsed to type {!r}.".format(
        content, expected_type
    )


@pytest.mark.parametrize("content", ["##foo", "//foo??", "...."])
def test_locator_invalid_content(content):
    with pytest.raises(ValueError, match=content):
        Locator(content)


@pytest.mark.parametrize("content", [123, 123.0, tuple(), list()])
def test_locator_unsupported_content(content):
    with pytest.raises(TypeError, match="'content' must be <class 'str'>"):
        Locator(content)


def test_platform(platform):
    assert platform is not None


def test_platform_unknown(pytester: Pytester):
    pytester.makeconftest(
        """
    import pytest

    @pytest.fixture(scope="session")
    def platform():
        return "unknown"
    """
    )

    testcase_path = pytester.makepyfile(
        """
    def test_default_executable_path(default_executable_path):
        assert default_executable_path is None

    def test_executable_path(executable_path):
        assert executable_path is None
    """
    )
    result = pytester.runpytest_inprocess(testcase_path)

    result.assert_outcomes(passed=2)


def test_executable_path_default(default_executable_path):
    assert default_executable_path is not None


def test_executable_path(default_executable_path, executable_path):
    assert default_executable_path == executable_path


def test_executable_path_commandoption(pytester: Pytester):
    testcase_path = pytester.makepyfile(
        """
    def test_executable_path(executable_path, default_executable_path):
        assert executable_path != default_executable_path
        assert executable_path == "path/to/chrome"
    """
    )
    result = pytester.runpytest_inprocess(testcase_path, "--executable-path", "path/to/chrome")

    result.assert_outcomes(passed=1)


def test_args_default(args):
    assert isinstance(args, list) and len(args) == 0


def test_args_commandoption(pytester: Pytester):
    testcase_path = pytester.makepyfile(
        """
    def test_args(args):
        assert args == ["--proxy-server=localhost:5555,direct://", "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8"]
    """
    )

    result = pytester.runpytest_inprocess(
        testcase_path,
        "--args",
        "proxy-server",
        "localhost:5555,direct://",
        "--args",
        "proxy-bypass-list",
        "192.0.0.1/8;10.0.0.1/8",
    )

    result.assert_outcomes(passed=1)


def test_options_default(options, executable_path):
    assert options["headless"] is False
    assert options["slowMo"] == 0.0
    assert options["executable_path"] == executable_path
    assert options["args"] == ["--window-size=800,600"]


def test_options_updating(pytester: Pytester):
    testcase_path = pytester.makepyfile(
        """
    import pytest

    @pytest.mark.options(devtools=True, headless=True)
    def test_options(options):
        assert options["devtools"] is True
        assert options["headless"] is True
    """
    )

    result = pytester.runpytest_inprocess(testcase_path)

    result.assert_outcomes(passed=1)


def test_asyncio_common_def(pytester: Pytester):
    testcase_path = pytester.makepyfile(
        """
    def test_demo(request):
        assert len(list(request.node.iter_markers("asyncio"))) == 0
    """
    )
    result = pytester.runpytest_inprocess(testcase_path)

    result.assert_outcomes(passed=1)
