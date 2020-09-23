import os
from typing import List, Optional, Union

from pydantic import BaseModel, validator

from pytest_pyppeteer.errors import PathNotAExecutableError


class ViewPort(BaseModel):
    """Keep the consistency of each page's viewport in a browser instance.

    One of the most important use is as the standard setting model for
    :py:class:`Options.defaultViewport`.
    """

    #: Page width in pixels. Defaults to ``800``.
    width: int = 800

    #: Page height in pixels. Defaults to ``600``.
    height: int = 600

    #: Specify device scale factor (can be thought of as dpr).
    #: Defaults to ``1.0``.
    deviceScaleFactor: float = 1.0

    #: Whether the ``meta viewport`` tag is taken into account.
    #: Defaults to ``False``.
    isMobile: bool = False

    #: Specifies if viewport supports touch events. Defaults to ``False``.
    hasTouch: bool = False

    #: Specifies if viewport is in landscape mode. Defaults to ``False``.
    isLandscape: bool = False


class Options(BaseModel):
    """The standard setting model for pyppeteer launcher."""

    #: Additional arguments to pass to the browser instance. The list
    #: of Chromium flags can be found
    #: `here <https://peter.sh/experiments/chromium-command-line-switches/>`_.
    #: Defaults to ``list()``.
    args: List[str] = list()

    #: Automatically close browser process when script completed.
    #: Defaults to ``True``.
    autoClose: bool = True

    #: Set a consistent viewport for each page. Defaults to a default
    #: :py:class:`ViewPort` instance. ``None`` means disables the
    #: default viewport.
    defaultViewport: Optional["ViewPort"] = ViewPort()

    #: Whether to auto-open a DevTools panel for each tab. If this
    #: option is ``True``, the ``headless`` option will be set ``False``.
    #: Defaults to ``False``.
    devtools: bool = False

    #: Whether to pipe the browser process stdout and stderr into
    #: ``process.stdout`` and ``process.stderr``. Defaults to ``False``.
    dumpio: bool = False

    #: Specify environment variables that will be visible to the
    #: browser. ``None`` means that same as python process.
    #: Defaults to ``None``.
    env: Optional[dict] = None

    #: Path to a Chromium or Chrome executable. ``None`` means use the
    #: default bundled Chromium. Defaults to ``None``.
    executablePath: Optional[str] = None

    #: Close the browser process on `Ctrl-C`. Defaults to ``True``.
    handleSIGINT: bool = True

    #: Close the browser process on `SIGTERM`. Defaults to ``True``.
    handleSIGTERM: bool = True

    #: Close the browser process on `SIGHUP`. Defaults to ``True``.
    handleSIGHUP: bool = True

    #: Whether to run browser in headless mode. Defaults to ``False``.
    headless: bool = False

    #: Whether to ignore HTTPS errors. Defaults to ``True``.
    ignoreHTTPSErrors: bool = True

    #: If ``True``, then do not use pyppeteer's default args. If a
    #: list is given, then filter out the given default args.
    #: Dangerous option; use with care. Defaults to ``False``.
    ignoreDefaultArgs: Union[bool, List[str]] = False

    #: Log level to print logs. ``None`` means that same as the root logger.
    #: Defaults to ``None``.
    logLevel: Union[int, str, None] = None

    #: Slow down operations by the specified amount of milliseconds.
    #: useful so that you can see what is going on. Defaults to ``0.0``.
    slowMo: float = 0.0

    #: Path to a
    #: `User Data Directory <https://chromium.googlesource.com/chromium/src/+/master/docs/user_data_dir.md>`_.
    #: Defaults to ``None``.
    userDataDir: Optional[str] = None

    class Config:
        """Control the behaviours of pydantic model."""

        #: whether to allow arbitrary user types for fields (they are
        #: validated simply by checking if the value is an instance
        #: of the type). If False, RuntimeError will be raised on model
        #: declaration.
        arbitrary_types_allowed = True

    @validator("executablePath", pre=True)
    def validate_executable_path(cls, path: Optional[str]) -> Optional[str]:
        """Validate that the specified ``executablePath`` must point
        to an executable.

        :param str path: path string.
        :return: path string.
        :raise PathNotAExecutableError: if path does not point to a
               executable file.
        """
        if path and not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise PathNotAExecutableError(path=os.path.abspath(path))
        return path
