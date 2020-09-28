import pytest


@pytest.fixture(scope="session")
def executable_path(executable_path):
    if executable_path is None:
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    return executable_path
