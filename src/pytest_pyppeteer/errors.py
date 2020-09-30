from typing import Any


class ErrorMixin:
    """The mixin for base exceptions.

    :param Any ctx: content variables.
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

    def __init__(self, path: str, **kwargs: Any) -> None:
        super(PathError, self).__init__(path=path)


class PathNotAExecutableError(PathError):
    code = "file.not_a_executable"
    msg_template = 'path "{path}" does not point to a executable file'


class LocatorError(Error):
    """The base-class for all locator-related exceptions.

    :param str path: locatore string.
    """

    def __init__(self, locator: str, **kwargs: Any) -> None:
        super(LocatorError, self).__init__(locator=locator)


class LocatorNotAValidSelectorOrXPathError(LocatorError):
    code = "locator.not_a_valid_selector_or_xpath"
    msg_template = 'locator "{locator}" is not a valid selector or xpath string.'


class ElementError(Error):
    """The base-class for all element-related exceptions.

    :param str locator: element locator string.
    """

    def __init__(self, locator: str, **kwargs: Any) -> None:
        super(ElementError, self).__init__(locator=locator, **kwargs)


class ElementNotExistError(ElementError):
    code = "element.not_exist"
    msg_template = 'Element "{locator}" not exist.'


class ElementTimeoutError(ElementError):
    code = "element.timeout"
    msg_template = (
        'Wait for element "{locator}" to {action} failed: timeout {timeout}ms exceeds.'
    )

    def __init__(self, locator: str, timeout: int, action: str = "appear") -> None:
        super(ElementTimeoutError, self).__init__(
            locator=locator, timeout=timeout, action=action
        )
