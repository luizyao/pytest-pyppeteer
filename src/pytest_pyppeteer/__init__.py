import sys

__version__ = "0.2.0"

if sys.version_info < (3, 5, 2):
    TYPE_CHECKING = False
else:
    # https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING
    from typing import TYPE_CHECKING
