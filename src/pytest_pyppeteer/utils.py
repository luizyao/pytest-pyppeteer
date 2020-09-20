import os
import sys

from pytest_pyppeteer.errors import PathNotAExecutableError

CHROME_EXECUTABLE = {
    "mac": r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "win64": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "win32": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
}


def existed_executable(path: str) -> str:
    """Filter the path which does not point to a executable file.

    The behaviors used in this plugin:

    * Called once the ``--executable-path`` option passed in from the command line.

    :param str path: a path string.
    :return: the path string point to the executable.
    :raise PathNotAExecutableError: if path does not point to a executable file.
    """
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        raise PathNotAExecutableError(path=os.path.abspath(path))
    return path


def current_platform() -> str:
    """Return current platform name.

    :return: the platform name. only be one of ``mac`` ``win64`` ``win32``.
    :raise OSError: if current platform is not supported.
    """
    if sys.platform.startswith("darwin"):
        return "mac"
    if sys.platform.startswith("win"):
        if sys.maxsize > 2 ** 31 - 1:
            return "win64"
        return "win32"
    raise OSError(
        'Unsupport platform: "{}"; Now only support "win64", "win32", "mac"'.format(
            sys.platform
        )
    )
