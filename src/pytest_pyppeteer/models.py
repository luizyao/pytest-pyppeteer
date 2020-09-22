import os
from typing import Optional

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

    #: Path to a Chromium or Chrome executable. ``None`` means use the
    #: default bundled Chromium.
    executablePath: Optional[str] = ...

    #: Set a consistent viewport for each page. Defaults to a default
    #: :py:class:`ViewPort` instance. ``None`` means disables the
    #: default viewport.
    defaultViewport: Optional["ViewPort"] = ViewPort()

    #: Whether to run browser in headless mode. Defaults to ``False``.
    headless: bool = False

    #: Whether to ignore HTTPS errors. Defaults to ``True``.
    ignoreHTTPSErrors: bool = True

    #: Slow down operations by the specified amount of milliseconds.
    #: useful so that you can see what is going on. Defaults to ``0.0``.
    slowMo: float = 0.0

    @validator("executablePath", pre=True)
    def executable_must_existed(cls, path: Optional[str]) -> Optional[str]:
        """Validate that the ``executablePath`` must be existed if it's
        not ``None``.

        :param str path: path string.
        :return: path string.
        :raise PathNotAExecutableError: if path does not point to a
               executable file.
        """
        if path and not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise PathNotAExecutableError(path=os.path.abspath(path))
        return path
