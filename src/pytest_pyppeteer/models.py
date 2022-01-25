"""All the models."""
from __future__ import annotations

from logging import getLogger

import cssselect
from attr import define, field, validators
from lxml import etree

logger = getLogger("pytest_pyppeteer.models")


@define
class Locator:
    """The locator.

    Attributes:
        content (str): The incoming locator content.
    """

    _type: str = field(init=False, validator=validators.in_(("css", "xpath")))
    content: str = field(validator=validators.instance_of(str))

    @content.validator
    def _is_valid_locator_content(self, _, value: str) -> None:
        """Check the validity of the locator content.

        Args:
            value (str): The locator content which needs to be validated.

        Raises:
            ValueError: The locator content neither a css nor an xpath string.
        """
        try:
            cssselect.parse(value)
        except cssselect.SelectorSyntaxError:
            pass
        else:
            self._type = "css"
            return

        try:
            etree.XPath(value)
        except etree.XPathSyntaxError:
            pass
        else:
            self._type = "xpath"
            return

        raise ValueError("Locator {!r} neither a css nor an xpath string.".format(value))
