Usage
=====

Command line options
--------------------

``--executable-path``
>>>>>>>>>>>>>>>>>>>>>

You can specify the path to a Chromium or Chrome executable. otherwise
pytest-pyppeteer will use the default installation location of Chrome
in current platform, but now only support ``win64``, ``win32`` and
``mac`` platform.

For other platforms, pyppeteer will downloads the recent version of
Chromium when called first time. If you don't prefer this behavior,
you can specify an exact path by override this fixture:

.. code-block:: python

    @pytest.fixture(scope="session")
    def executable_path(executable_path):
        if executable_path is None:
            return "path/to/Chrome/or/Chromium"
        return executable_path

.. note::

    The default installation location of Chrome in different platform:

    * ``win64``: C:\Program Files\Google\Chrome\Application\chrome.exe
    * ``win32``: C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    * ``mac``: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome

``--headless``
>>>>>>>>>>>>>>

Run browser in headless mode.

``--args``
>>>>>>>>>>

Additional args to pass to the browser instance.

For example, specify a proxy:

.. code-block:: bash

    $ pytest --args proxy-server "localhost:5555,direct://" --args proxy-bypass-list "192.0.0.1/8;10.0.0.1/8"

Or by override the ``args`` fixture:

.. code-block:: python

    @pytest.fixture(scope="session")
    def args(args) -> List[str]:
        return args + [
            "--proxy-server=localhost:5555,direct://",
            "--proxy-bypass-list=192.0.0.1/8;10.0.0.1/8",
        ]

``--window-size``
>>>>>>>>>>>>>>>>>

The default browser size is 800*600, you can use this option to change this behavior:

.. code-block:: bash

    $ pytest --window-size 1200 800

``--window-size 0 0`` means to starts the browser maximized.


No matter selector or xpath
---------------------------

``pyppeteer`` fixture provide a ``pytest_pyppeteer.models.Browser`` instance, its
usage is almost the same as ``pyppeteer.browser.Browser``, except that it provides
a new instance method: ``new_page()``, which is similar to ``newPage()``, but it
returns a ``pytest_pyppeteer.models.Page`` instead of ``pyppeteer.page.Page``.

``pytest_pyppeteer.models.Page``'s usage is also the same as ``pyppeteer.page.Page``,
but it provides some new instance methods, and override some methods. For example,
you can query an element by selector or xpath in just same method ``query_locator``
instead of original ``querySelector`` and ``xpath``.

You can also get an original ``Page`` by ``pyppeteer.newPage()``.

``options`` marker
------------------

You can override some command line options in the specified test.

For example, auto-open a DevTools panel:

.. code-block:: python

    import asyncio

    import pytest


    @pytest.mark.options(devtools=True)
    async def test_marker(pyppeteer):
        await pyppeteer.new_page()
        await asyncio.sleep(2)

.. image:: image/options_marker.gif
   :alt: options_marker
   :align: left
