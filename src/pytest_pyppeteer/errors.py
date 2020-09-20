from typing import Any


class ErrorMixin:
    """The mixin for base exceptions.

    :param Any ctx: content veriables.
    """

    #: Type identification code.
    code: str
    #: Error message template.
    msg_template: str

    def __init__(self, **ctx: Any) -> None:
        self.__dict__ = ctx

    def __str__(self) -> str:
        return self.msg_template.format(**self.__dict__)


class Error(ErrorMixin, Exception):
    """Base-class for all exceptions raised by this plugin."""


class PathError(Error):
    """The base-class for all path-related exceptions.

    :param str path: path string.
    """

    def __init__(self, path: str) -> None:
        super(PathError, self).__init__(path=path)


class PathNotAExecutableError(PathError):
    code = "file.not_a_executable"
    msg_template = 'path "{path}" does not point to a executable file'
