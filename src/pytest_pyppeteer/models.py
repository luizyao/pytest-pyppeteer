import os
from typing import Optional

from pydantic import BaseSettings, validator

from pytest_pyppeteer.errors import PathNotAExecutableError


class Options(BaseSettings):
    """The options of Chrome launcher."""

    #: Path to a Chromium or Chrome executable.
    executablePath: Optional[str] = ...

    #: Whether to run browser in headless mode. Defaults to ``False``.
    headless: bool = False

    #: Whether to ignore HTTPS errors. Default is ``True``.
    ignoreHTTPSErrors: bool = True

    @validator("executablePath", pre=True)
    def executable_must_existed(cls, path: Optional[str]) -> Optional[str]:
        """Validate that the executable must existed.

        :param str path: path string.
        :return: path string.
        :raise PathNotAExecutableError: if path does not point to a executable file.
        """
        if path and not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise PathNotAExecutableError(path=os.path.abspath(path))
        return path
