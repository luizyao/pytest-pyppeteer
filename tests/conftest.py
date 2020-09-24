import pytest


@pytest.fixture(scope="session")
def executable_path(executable_path):
    return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
