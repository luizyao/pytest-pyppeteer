import pytest


@pytest.fixture(scope="session")
def executable_path(executable_path):
    if executable_path is None:
        return (
            r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
        )
    return executable_path
