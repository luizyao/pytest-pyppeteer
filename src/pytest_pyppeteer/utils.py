import sys

CHROME_EXECUTABLE = {
    "mac": r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "win64": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "win32": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
}


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
